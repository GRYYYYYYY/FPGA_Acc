#pragma once

#include "dieroute.hpp"

namespace dieroute {

// V1 is a capacity-reservation protocol, not an electrical RR graph. Boundary
// entries must describe disjoint reservable resources; raw RR edges do not.
enum class CorridorStatus : std::uint32_t {
    ready, committed, released, unreachable, invalid, stale, capacity,
    version_exhausted, slot_busy, handle_mismatch
};

struct CorridorPlan {
    CorridorStatus status = CorridorStatus::invalid;
    std::uint32_t task_id = 0;
    std::uint16_t source_die = 0, sink_die = 0, demand = 0, length = 0;
    std::uint16_t boundaries[MAX_DIES - 1]{};
    std::uint32_t observed_versions[MAX_DIES - 1]{};
    std::uint64_t score_q = 0;
};

// This slot is authoritative state. Release requests supply its generation and
// task ID, not a client-controlled copy of its contents. Reuse cannot let an old
// release cancel a new reservation (ABA). Active plans are never overwritten.
struct ReservationSlot {
    CorridorPlan plan{};
    std::uint32_t generation = 0;
    bool active = false;
};

CorridorPlan plan_corridor(const Boundary* boundaries, std::uint32_t boundary_count,
                          std::uint32_t die_count, const CrossDieTask& task);

CorridorStatus reserve_corridor(Boundary* boundaries, std::uint32_t boundary_count,
                               std::uint32_t die_count, const CorridorPlan& plan,
                               ReservationSlot& slot);

CorridorStatus release_corridor(Boundary* boundaries, std::uint32_t boundary_count,
                               std::uint32_t die_count, std::uint32_t task_id,
                               std::uint32_t generation, ReservationSlot& slot);

} // namespace dieroute
