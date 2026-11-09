#pragma once
#include <cstdint>
namespace routecast {
constexpr std::uint32_t MAX_TILES=4096, MAX_EDGES=32768, MAX_DIRTY=2048, MAX_CLASSES=8;
constexpr std::uint32_t MAX_HOPS=256;
struct Tile { std::uint32_t edge_begin; std::uint16_t edge_count; std::uint16_t x,y; };
struct EdgeTemplate { std::uint32_t dst; std::uint16_t segment_class; std::uint16_t capacity; std::uint16_t direction; std::uint16_t pin_class; };
struct DirtyConnection { std::uint32_t source_tile,sink_tile; std::uint16_t demand_q,flags; };
// Additive batch only: callers must not replay connections already accounted for.
// Failure leaves that connection's demand unchanged; earlier successes remain.
struct SketchMetrics {
 std::uint64_t updates; std::uint64_t edge_visits;
 std::uint32_t saturated; std::uint32_t max_demand_q;
 std::uint32_t completed, failed, invalid_connections, overflow_rejections;
 std::uint32_t invalid_batch;
};
extern "C" void routecast_kernel(const Tile tiles[MAX_TILES], const EdgeTemplate edges[MAX_EDGES],
 const DirtyConnection dirty[MAX_DIRTY], std::uint32_t demand_q[MAX_EDGES],
 std::uint32_t tile_count, std::uint32_t edge_count, std::uint32_t dirty_count,
 std::uint32_t hop_limit, SketchMetrics* metrics);
}
