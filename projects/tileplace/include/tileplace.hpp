#pragma once
#include <cstdint>

namespace tileplace {
constexpr std::uint32_t MAX_INSTANCES = 512;
constexpr std::uint32_t MAX_PAGES = 64;
constexpr std::uint32_t RESOURCE_TYPES = 3; // CLB, BRAM, DSP

struct Instance {
    std::uint16_t x, y;
    std::uint16_t resource_type;
    std::uint16_t criticality_q;
    std::uint16_t region_xmin, region_ymin, region_xmax, region_ymax;
    std::uint16_t cascade_id;
};
struct Page {
    std::uint16_t xmin, ymin, xmax, ymax;
    std::uint16_t capacity[RESOURCE_TYPES];
    std::uint16_t used[RESOURCE_TYPES];
};
struct PlacementMetrics {
    std::uint32_t placed;
    std::uint32_t unplaced;
    std::uint64_t wire_cost_q;
    std::uint64_t timing_cost_q;
    std::uint64_t boundary_cost_q;
};

extern "C" void tileplace_kernel(
    const Instance instances[MAX_INSTANCES], Page pages[MAX_PAGES],
    std::uint16_t assignment[MAX_INSTANCES], std::uint16_t placed_x[MAX_INSTANCES],
    std::uint16_t placed_y[MAX_INSTANCES], std::uint32_t instance_count,
    std::uint32_t page_count, PlacementMetrics* metrics);
}
