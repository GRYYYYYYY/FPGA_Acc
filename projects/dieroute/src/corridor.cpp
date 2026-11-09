#include "corridor.hpp"

#include <cstdint>
#include <limits>

namespace dieroute {
namespace {
constexpr std::uint32_t invalid_id = 0xffffffffU;
constexpr std::uint64_t infinity = std::numeric_limits<std::uint64_t>::max();

bool valid_topology(const Boundary* boundaries, std::uint32_t count, std::uint32_t dies) {
    if (!boundaries || count > MAX_BOUNDARIES || dies == 0 || dies > MAX_DIES) return false;
    for (std::uint32_t b = 0; b < count; ++b) {
        const auto& x = boundaries[b];
        if (x.src_die >= dies || x.dst_die >= dies || x.src_die == x.dst_die ||
            x.reserved > x.capacity) return false;
    }
    return true;
}

bool valid_plan(const Boundary* boundaries, std::uint32_t count, std::uint32_t dies,
                const CorridorPlan& plan) {
    if (!valid_topology(boundaries, count, dies) || plan.source_die >= dies ||
        plan.sink_die >= dies || plan.demand == 0 || plan.length >= dies) return false;
    bool visited[MAX_DIES]{};
    auto current = plan.source_die;
    visited[current] = true;
    for (std::uint32_t i = 0; i < plan.length; ++i) {
        const auto id = plan.boundaries[i];
        if (id >= count) return false;
        const auto& b = boundaries[id];
        if (b.src_die != current || visited[b.dst_die]) return false;
        current = b.dst_die;
        visited[current] = true;
    }
    return current == plan.sink_die;
}

std::uint64_t cost(const Boundary& b, const CrossDieTask& t) {
    // Strictly positive costs make simple die paths sufficient for this coarse
    // model. Electrical routing may need a different corridor and must replan.
    return 64 + (static_cast<std::uint64_t>(b.reserved) + t.demand) * 65536 / b.capacity +
           b.history_q + static_cast<std::uint64_t>(b.delay_q) * t.criticality_q / 65535;
}
} // namespace

CorridorPlan plan_corridor(const Boundary* boundaries, std::uint32_t boundary_count,
                          std::uint32_t die_count, const CrossDieTask& task) {
    CorridorPlan plan{};
    plan.task_id = task.id;
    plan.source_die = task.src_die;
    plan.sink_die = task.dst_die;
    plan.demand = task.demand;
    if (!valid_topology(boundaries, boundary_count, die_count) || task.src_die >= die_count ||
        task.dst_die >= die_count || task.demand == 0) return plan;
    std::uint64_t distance[MAX_DIES];
    std::uint32_t hops[MAX_DIES], predecessor[MAX_DIES];
    bool closed[MAX_DIES]{};
    for (std::uint32_t d = 0; d < MAX_DIES; ++d) {
        distance[d] = infinity;
        hops[d] = predecessor[d] = invalid_id;
    }
    distance[task.src_die] = 0;
    hops[task.src_die] = 0;
    for (std::uint32_t iteration = 0; iteration < die_count; ++iteration) {
        std::uint32_t current = invalid_id;
        for (std::uint32_t d = 0; d < die_count; ++d) {
            if (closed[d] || distance[d] == infinity) continue;
            if (current == invalid_id || distance[d] < distance[current] ||
                (distance[d] == distance[current] && hops[d] < hops[current])) current = d;
        }
        if (current == invalid_id) break;
        closed[current] = true;
        if (current == task.dst_die) break;
        for (std::uint32_t b = 0; b < boundary_count; ++b) {
            const auto& x = boundaries[b];
            if (x.src_die != current || closed[x.dst_die] || x.capacity == 0 ||
                static_cast<std::uint32_t>(x.reserved) + task.demand > x.capacity) continue;
            const auto candidate = distance[current] + cost(x, task);
            const auto next_hops = hops[current] + 1;
            const auto dst = x.dst_die;
            if (candidate < distance[dst] || (candidate == distance[dst] &&
                (next_hops < hops[dst] || (next_hops == hops[dst] && b < predecessor[dst])))) {
                distance[dst] = candidate;
                hops[dst] = next_hops;
                predecessor[dst] = b;
            }
        }
    }
    if (!closed[task.dst_die]) {
        plan.status = CorridorStatus::unreachable;
        return plan;
    }
    plan.length = static_cast<std::uint16_t>(hops[task.dst_die]);
    plan.score_q = distance[task.dst_die];
    auto die = task.dst_die;
    for (std::uint32_t remaining = plan.length; remaining > 0; --remaining) {
        const auto b = predecessor[die];
        plan.boundaries[remaining - 1] = static_cast<std::uint16_t>(b);
        plan.observed_versions[remaining - 1] = boundaries[b].version;
        die = boundaries[b].src_die;
    }
    plan.status = CorridorStatus::ready;
    return plan;
}

CorridorStatus reserve_corridor(Boundary* boundaries, std::uint32_t boundary_count,
                               std::uint32_t die_count, const CorridorPlan& plan,
                               ReservationSlot& slot) {
    if (plan.status != CorridorStatus::ready ||
        !valid_plan(boundaries, boundary_count, die_count, plan)) return CorridorStatus::invalid;
    if (slot.active) return CorridorStatus::slot_busy;
    if (slot.generation == invalid_id) return CorridorStatus::version_exhausted;
    // Validate all hops before writing any authoritative boundary.
    for (std::uint32_t i = 0; i < plan.length; ++i) {
        const auto& b = boundaries[plan.boundaries[i]];
        if (b.version != plan.observed_versions[i]) return CorridorStatus::stale;
        if (static_cast<std::uint32_t>(b.reserved) + plan.demand > b.capacity)
            return CorridorStatus::capacity;
        if (b.version == invalid_id) return CorridorStatus::version_exhausted;
    }
    for (std::uint32_t i = 0; i < plan.length; ++i) {
        auto& b = boundaries[plan.boundaries[i]];
        b.reserved = static_cast<std::uint16_t>(b.reserved + plan.demand);
        ++b.version;
    }
    slot.plan = plan;
    slot.plan.status = CorridorStatus::committed;
    ++slot.generation;
    slot.active = true;
    return CorridorStatus::committed;
}

CorridorStatus release_corridor(Boundary* boundaries, std::uint32_t boundary_count,
                               std::uint32_t die_count, std::uint32_t task_id,
                               std::uint32_t generation, ReservationSlot& slot) {
    if (!slot.active || slot.generation != generation || slot.plan.task_id != task_id)
        return CorridorStatus::handle_mismatch;
    if (slot.plan.status != CorridorStatus::committed ||
        !valid_plan(boundaries, boundary_count, die_count, slot.plan)) return CorridorStatus::invalid;
    for (std::uint32_t i = 0; i < slot.plan.length; ++i) {
        const auto& b = boundaries[slot.plan.boundaries[i]];
        if (b.reserved < slot.plan.demand) return CorridorStatus::invalid;
        if (b.version == invalid_id) return CorridorStatus::version_exhausted;
    }
    for (std::uint32_t i = 0; i < slot.plan.length; ++i) {
        auto& b = boundaries[slot.plan.boundaries[i]];
        b.reserved = static_cast<std::uint16_t>(b.reserved - slot.plan.demand);
        ++b.version;
    }
    slot.active = false;
    slot.plan.status = CorridorStatus::released;
    return CorridorStatus::released;
}
} // namespace dieroute
