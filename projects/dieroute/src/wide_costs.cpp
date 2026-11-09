#include "wide_costs.hpp"
#include <algorithm>
#include <limits>
#include <stdexcept>

namespace dieroute {
namespace {
__extension__ typedef unsigned __int128 U128;
std::uint64_t narrow(U128 value) {
    if (value > std::numeric_limits<std::uint64_t>::max())
        throw std::overflow_error("wide congestion cost exceeds u64; no saturation allowed");
    return static_cast<std::uint64_t>(value);
}
}
std::uint64_t grow_present(std::uint64_t present, std::uint16_t multiplier_q) {
    if (!multiplier_q) throw std::invalid_argument("zero congestion multiplier");
    return std::max<std::uint64_t>(1, narrow((U128(present) * multiplier_q + 128) / 256));
}
void update_wide_costs(std::vector<persistroute::Resource>& resources,
                       std::vector<WideCost>& costs, std::uint64_t present,
                       std::uint16_t history_step, const RoutingPolicy* policy) {
    if (resources.size() != costs.size()) throw std::invalid_argument("wide cost count mismatch");
    // Validate all arithmetic/versions before changing any authoritative state.
    auto next = costs;
    for (std::size_t i = 0; i < resources.size(); ++i) {
        if(policy && policy->frozen(i))continue;
        const auto& r = resources[i];
        const auto over = r.occupancy > r.capacity ? r.occupancy - r.capacity : 0U;
        next[i] = {present, narrow(U128(costs[i].history_q) + U128(history_step) * over)};
        if ((next[i].present_q != costs[i].present_q || next[i].history_q != costs[i].history_q) &&
            r.version == std::numeric_limits<std::uint32_t>::max())
            throw std::overflow_error("wide cost update would wrap resource version");
    }
    for (std::size_t i = 0; i < resources.size(); ++i) {
        if (next[i].present_q != costs[i].present_q || next[i].history_q != costs[i].history_q)
            ++resources[i].version;
    }
    costs.swap(next);
}
} // namespace dieroute
