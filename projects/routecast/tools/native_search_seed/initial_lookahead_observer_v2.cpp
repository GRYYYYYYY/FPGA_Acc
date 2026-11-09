#include "route_utils.h"
#include "globals.h"
#include "route_net.h"
#include "timing_info.h"
#include "timing_util.h"
#include "clustered_netlist_utils.h"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <stdexcept>

static uint32_t bits(float value) {
    uint32_t word;
    static_assert(sizeof(word) == sizeof(value), "float32 required");
    std::memcpy(&word, &value, sizeof(word));
    return word;
}
extern "C" float REAL(const SetupHoldTimingInfo*, const ClusteredPinAtomPinsLookup&, float, float, ParentNetId, ParentPinId, bool);
extern "C" float WRAP(const SetupHoldTimingInfo* timing, const ClusteredPinAtomPinsLookup& lookup, float maximum, float exponent, ParentNetId net, ParentPinId pin, bool flat) {
    const char* timing_path = std::getenv("ROUTECAST_INITIAL_TIMING");
    if (!timing_path) return REAL(timing, lookup, maximum, exponent, net, pin, flat);
    const char* criticality_path = std::getenv("ROUTECAST_INITIAL_CRITICALITY");
    if (!criticality_path || flat || !timing) throw std::runtime_error("requires timing, clustered mode and two explicit output paths");
    FILE* criticality = std::fopen(criticality_path, "wx");
    FILE* detail = std::fopen(timing_path, "wx");
    if (!criticality || !detail) throw std::runtime_error("exclusive observer output open failed");
    const auto& list = g_vpr_ctx.clustering().clb_nlist;
    unsigned long long sequence = 0, atom_rows = 0;
    std::fprintf(detail, "H\t1\t%zu\t%zu\t%d\t%.9g\t%.9g\n", size_t(net), size_t(pin), int(flat), double(maximum), double(exponent));
    for (auto n : list.nets()) for (auto p : list.net_sinks(n)) {
        ++sequence;
        const ParentNetId parent_net{int(size_t(n))};
        const ParentPinId parent_pin{int(size_t(p))};
        float transformed = REAL(timing, lookup, maximum, exponent, parent_net, parent_pin, false);
        // Preserve the original observer's criticality bytes and enumeration.
        std::fprintf(criticality, "C\t%llu\t%zu\t%zu\t%d\t%.9g\t%.9g\t%.9g\t%d\t%d\n", sequence, size_t(n), size_t(p), list.pin_net_index(p), double(transformed), double(maximum), double(exponent), int(list.net_is_ignored(n)), int(list.net_is_global(n)));
        float manual_slack = std::numeric_limits<float>::infinity();
        float manual_criticality = 0.f;
        size_t atom_count = 0;
        for (auto atom : lookup.connected_atom_pins(p)) {
            float slack = timing->setup_pin_slack(atom);
            float crit = timing->setup_pin_criticality(atom);
            manual_slack = std::min(manual_slack, slack);
            manual_criticality = std::max(manual_criticality, crit);
            ++atom_count;
            ++atom_rows;
            std::fprintf(detail, "A\t%llu\t%zu\t%zu\t%d\t%zu\t%.9g\t%08x\t%.9g\t%08x\n", sequence, size_t(n), size_t(p), list.pin_net_index(p), size_t(atom), double(slack), bits(slack), double(crit), bits(crit));
        }
        float native_slack = calculate_clb_net_pin_setup_slack(*timing, lookup, p);
        float raw_criticality = calculate_clb_net_pin_criticality(*timing, lookup, parent_pin, false);
        if (bits(native_slack) != bits(manual_slack) || bits(raw_criticality) != bits(manual_criticality)) throw std::runtime_error("native/manual atom aggregation mismatch");
        std::fprintf(detail, "S\t%llu\t%zu\t%zu\t%d\t%zu\t%.9g\t%08x\t%.9g\t%08x\t%.9g\t%08x\t%d\t%d\t%d\n", sequence, size_t(n), size_t(p), list.pin_net_index(p), atom_count, double(native_slack), bits(native_slack), double(raw_criticality), bits(raw_criticality), double(transformed), bits(transformed), int(list.net_is_ignored(n)), int(list.net_is_global(n)), int(g_vpr_ctx.routing().is_clock_net[parent_net]));
    }
    bool failed = std::ferror(criticality) || std::ferror(detail);
    int a = std::fclose(criticality), b = std::fclose(detail);
    if (failed || a || b) std::abort();
    std::printf("ROUTECAST INITIAL CRITICALITY SNAPSHOT %llu first_net=%zu first_pin=%zu\n", sequence, size_t(net), size_t(pin));
    std::printf("ROUTECAST INITIAL TIMING SNAPSHOT %llu atom_rows=%llu exit_before_first_getter_returns=1\n", sequence, atom_rows);
    std::fflush(stdout);
    std::exit(0);
}

extern "C" void DELAY_ORIGINAL(const RouterLookahead&, const Netlist<>&, const vtr::vector<ParentNetId, std::vector<RRNodeId>>&, NetPinsMatrix<float>&, const RRGraphView&, bool);
extern "C" void DELAY_HOOK(const RouterLookahead& lookahead, const Netlist<>& list, const vtr::vector<ParentNetId, std::vector<RRNodeId>>& terminals, NetPinsMatrix<float>& delays, const RRGraphView& graph, bool flat) {
    DELAY_ORIGINAL(lookahead, list, terminals, delays, graph, flat);
    const char* path = std::getenv("ROUTECAST_INITIAL_LOOKAHEAD_DELAY");
    if (!path) return;
    if (flat) throw std::runtime_error("lookahead observer requires clustered mode");
    FILE* out = std::fopen(path, "wx");
    if (!out) throw std::runtime_error("exclusive lookahead output open failed");
    unsigned long long sequence = 0;
    for (auto net : list.nets()) {
        if (list.net_is_ignored(net)) continue;
        for (auto pin : list.net_sinks(net)) {
            const int local = list.pin_net_index(pin);
            const float delay = delays[net][local];
            if (!std::isfinite(delay)) throw std::runtime_error("nonfinite initialized lookahead delay");
            std::fprintf(out, "D\t%llu\t%zu\t%zu\t%d\t%.9g\t%08x\n", ++sequence, size_t(net), size_t(pin), local, double(delay), bits(delay));
        }
    }
    const bool failed = std::ferror(out);
    if (std::fclose(out) || failed) std::abort();
    std::printf("ROUTECAST INITIAL LOOKAHEAD DELAY SNAPSHOT %llu after_original_init=1\n", sequence);
}
