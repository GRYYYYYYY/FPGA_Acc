#include "corridor.hpp"

#include <array>
#include <cstring>
#include <iostream>
#include <limits>
#include <random>
#include <stdexcept>

using namespace dieroute;
using Boundaries = std::array<Boundary, MAX_BOUNDARIES>;

void require(bool pass, const char* description) {
    if (!pass) throw std::runtime_error(description);
}

std::uint64_t exhaustive(const Boundaries& b, unsigned count, const CrossDieTask& t,
                         unsigned die, unsigned visited) {
    if (die == t.dst_die) return 0;
    auto best = std::numeric_limits<std::uint64_t>::max();
    for (unsigned i = 0; i < count; ++i) {
        const auto& edge = b[i];
        if (edge.src_die != die || (visited & (1U << edge.dst_die)) || edge.capacity == 0 ||
            unsigned(edge.reserved) + t.demand > edge.capacity) continue;
        const auto tail = exhaustive(b, count, t, edge.dst_die, visited | (1U << edge.dst_die));
        if (tail == std::numeric_limits<std::uint64_t>::max()) continue;
        const std::uint64_t score = 64 + (std::uint64_t(edge.reserved) + t.demand) * 65536 / edge.capacity +
            edge.history_q + std::uint64_t(edge.delay_q) * t.criticality_q / 65535;
        if (tail + score < best) best = tail + score;
    }
    return best;
}

void protocol_tests() {
    Boundaries b{};
    b[0] = {0, 1, 3, 0, 100, 0, 0};
    b[1] = {1, 2, 3, 0, 100, 0, 0};
    b[2] = {0, 2, 1, 0, 60000, 0, 0};
    CrossDieTask t{7, 0, 2, 65535, 1, 0};
    const auto p = plan_corridor(b.data(), 3, 3, t);
    require(p.status == CorridorStatus::ready && p.length == 2 &&
            p.boundaries[0] == 0 && p.boundaries[1] == 1, "minimum cost multi-hop corridor");
    ReservationSlot slot{}, other{};
    require(reserve_corridor(b.data(), 3, 3, p, slot) == CorridorStatus::committed, "commit");
    require(b[0].reserved == 1 && b[1].reserved == 1 && b[0].version == 1 &&
            b[1].version == 1 && b[2].version == 0, "exact commit updates");
    auto before = b;
    require(reserve_corridor(b.data(), 3, 3, p, other) == CorridorStatus::stale, "stale shadow rejected");
    require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0 && !other.active,
            "failed commit unchanged");
    auto fresh = plan_corridor(b.data(), 3, 3, t);
    require(reserve_corridor(b.data(), 3, 3, fresh, other) == CorridorStatus::committed,
            "replay on fresh shadow");
    require(release_corridor(b.data(), 3, 3, 7, 1, slot) == CorridorStatus::released,
            "release after unrelated commit does not require stale versions");
    require(b[0].reserved == 1 && b[1].reserved == 1, "preserve other reservation");
    before = b;
    require(release_corridor(b.data(), 3, 3, 7, 1, slot) == CorridorStatus::handle_mismatch,
            "duplicate release rejected");
    require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0, "duplicate release no writes");
    fresh = plan_corridor(b.data(), 3, 3, t);
    require(reserve_corridor(b.data(), 3, 3, fresh, slot) == CorridorStatus::committed &&
            slot.generation == 2, "slot reuse increments generation");
    before = b;
    require(release_corridor(b.data(), 3, 3, 7, 1, slot) == CorridorStatus::handle_mismatch,
            "ABA release rejected");
    require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0, "ABA no writes");

    // A conflict on the LAST hop must not update the first hop.
    b[2].capacity = 0; // force two hops even when the intermediate boundary is busy
    ReservationSlot late{};
    fresh = plan_corridor(b.data(), 3, 3, t);
    require(fresh.length == 2, "late-hop fixture uses two boundaries");
    ++b[1].version;
    before = b;
    require(reserve_corridor(b.data(), 3, 3, fresh, late) == CorridorStatus::stale,
            "late-hop conflict");
    require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0, "late-hop atomicity");
    fresh = plan_corridor(b.data(), 3, 3, t);
    fresh.boundaries[1] = fresh.boundaries[0];
    require(reserve_corridor(b.data(), 3, 3, fresh, late) == CorridorStatus::invalid,
            "forged repeated boundary rejected");
    require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0, "malformed plan no writes");

    b[1].capacity = b[1].reserved;
    t.demand = 2;
    require(plan_corridor(b.data(), 3, 3, t).status == CorridorStatus::unreachable,
            "capacity prevents partial corridor");
    t.src_die = 8;
    require(plan_corridor(b.data(), 3, 3, t).status == CorridorStatus::invalid, "invalid die");
    t = {8, 1, 1, 0, 1, 0};
    const auto local = plan_corridor(b.data(), 3, 3, t);
    require(local.status == CorridorStatus::ready && local.length == 0, "local task zero boundary");
    before = b;
    require(reserve_corridor(b.data(), 3, 3, local, late) == CorridorStatus::committed, "local reserve");
    require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0, "local task no boundary writes");

    Boundaries exhausted{};
    exhausted[0] = {0, 1, 65535, 65534, 65535, 65535, 0xffffffffU};
    t = {0, 0, 1, 65535, 1, 0};
    auto last = plan_corridor(exhausted.data(), 1, 2, t);
    ReservationSlot empty{};
    require(reserve_corridor(exhausted.data(), 1, 2, last, empty) == CorridorStatus::version_exhausted,
            "version must not wrap");
    t.demand = 65535;
    require(plan_corridor(exhausted.data(), 1, 2, t).status == CorridorStatus::unreachable,
            "capacity arithmetic must not wrap");
}

void differential_tests() {
    std::mt19937 rng(0xD1E2026);
    for (unsigned trial = 0; trial < 2000; ++trial) {
        Boundaries b{};
        const unsigned dies = 2 + rng() % 4;
        unsigned count = 0;
        for (unsigned a = 0; a < dies; ++a) for (unsigned d = 0; d < dies; ++d) {
            if (a == d || rng() % 3 == 0) continue;
            const auto capacity = static_cast<std::uint16_t>(rng() % 6);
            b[count++] = {static_cast<std::uint16_t>(a), static_cast<std::uint16_t>(d), capacity,
                          static_cast<std::uint16_t>(rng() % (capacity + 1)),
                          static_cast<std::uint16_t>(rng()), static_cast<std::uint16_t>(rng()), 0};
        }
        CrossDieTask t{trial, static_cast<std::uint16_t>(rng() % dies),
                       static_cast<std::uint16_t>(rng() % dies),
                       static_cast<std::uint16_t>(rng()), static_cast<std::uint16_t>(1 + rng() % 3), 0};
        const auto golden = exhaustive(b, count, t, t.src_die, 1U << t.src_die);
        const auto before = b;
        const auto p = plan_corridor(b.data(), count, dies, t);
        require(std::memcmp(b.data(), before.data(), sizeof(b)) == 0, "planning must be read-only");
        if (golden == std::numeric_limits<std::uint64_t>::max()) {
            require(p.status == CorridorStatus::unreachable, "exhaustive reachability");
            continue;
        }
        require(p.status == CorridorStatus::ready && p.score_q == golden, "exhaustive minimum cost");
        for (unsigned repeat = 0; repeat < 5; ++repeat) {
            const auto again = plan_corridor(b.data(), count, dies, t);
            require(again.length == p.length && again.score_q == p.score_q, "deterministic plan");
            for (unsigned j = 0; j < p.length; ++j)
                require(again.boundaries[j] == p.boundaries[j], "deterministic path");
        }
        ReservationSlot slot{};
        require(reserve_corridor(b.data(), count, dies, p, slot) == CorridorStatus::committed,
                "valid random plan commits");
        require(release_corridor(b.data(), count, dies, t.id, slot.generation, slot) == CorridorStatus::released,
                "valid random plan releases");
        for (unsigned i = 0; i < count; ++i) {
            require(b[i].reserved == before[i].reserved, "release restores capacity");
            bool touched = false;
            for (unsigned j = 0; j < p.length; ++j) touched |= p.boundaries[j] == i;
            require(b[i].version == (touched ? 2U : 0U), "versions exactly once per successful update");
        }
    }
}

int main() {
    try {
        protocol_tests();
        differential_tests();
        std::cout << "corridor_tb: PASS (atomic reserve/release, stale replay, ABA, 2000 exhaustive comparisons)\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
