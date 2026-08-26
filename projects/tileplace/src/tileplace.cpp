#include "tileplace.hpp"
#include <cstdint>

namespace tileplace {
namespace {
std::uint32_t abs_diff(std::uint16_t a, std::uint16_t b) { return a > b ? a - b : b - a; }
bool intersects(const Instance& i, const Page& p) {
    return !(p.xmax < i.region_xmin || p.xmin > i.region_xmax ||
             p.ymax < i.region_ymin || p.ymin > i.region_ymax);
}
}

extern "C" void tileplace_kernel(
    const Instance instances[MAX_INSTANCES], Page pages[MAX_PAGES],
    std::uint16_t assignment[MAX_INSTANCES], std::uint16_t placed_x[MAX_INSTANCES],
    std::uint16_t placed_y[MAX_INSTANCES], std::uint32_t instance_count,
    std::uint32_t page_count, PlacementMetrics* metrics) {
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=instances bundle=gmem0
#pragma HLS INTERFACE m_axi port=pages bundle=gmem1
#pragma HLS INTERFACE m_axi port=assignment bundle=gmem2
#pragma HLS INTERFACE m_axi port=placed_x bundle=gmem2
#pragma HLS INTERFACE m_axi port=placed_y bundle=gmem2
#pragma HLS INTERFACE s_axilite port=instance_count bundle=control
#pragma HLS INTERFACE s_axilite port=page_count bundle=control
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem3
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
    PlacementMetrics out{};
    if (instance_count > MAX_INSTANCES || page_count > MAX_PAGES) { *metrics = out; return; }
    for (std::uint32_t i = 0; i < instance_count; ++i) {
        const Instance inst = instances[i];
        std::uint64_t best = ~std::uint64_t{0};
        std::uint16_t best_page = 0xffff;
        for (std::uint32_t p = 0; p < page_count; ++p) {
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
            if (inst.resource_type >= RESOURCE_TYPES || !intersects(inst, pages[p]) ||
                pages[p].used[inst.resource_type] >= pages[p].capacity[inst.resource_type]) continue;
            const std::uint16_t cx = (pages[p].xmin + pages[p].xmax) / 2;
            const std::uint16_t cy = (pages[p].ymin + pages[p].ymax) / 2;
            const std::uint32_t distance = abs_diff(inst.x, cx) + abs_diff(inst.y, cy);
            const std::uint32_t boundary = (inst.x < pages[p].xmin || inst.x > pages[p].xmax ||
                                            inst.y < pages[p].ymin || inst.y > pages[p].ymax) ? 256 : 0;
            const std::uint64_t timing = static_cast<std::uint64_t>(distance) * inst.criticality_q;
            const std::uint64_t quota = static_cast<std::uint64_t>(pages[p].used[inst.resource_type]) * 128;
            const std::uint64_t score = static_cast<std::uint64_t>(distance) * 256 + timing + boundary + quota;
            if (score < best || (score == best && p < best_page)) { best = score; best_page = p; }
        }
        assignment[i] = best_page;
        if (best_page == 0xffff) { placed_x[i] = placed_y[i] = 0xffff; ++out.unplaced; continue; }
        Page& page = pages[best_page];
        const std::uint16_t slot = page.used[inst.resource_type]++;
        const std::uint16_t width = page.xmax - page.xmin + 1;
        placed_x[i] = static_cast<std::uint16_t>(page.xmin + slot % width);
        placed_y[i] = static_cast<std::uint16_t>(page.ymin + slot / width);
        const std::uint32_t distance = abs_diff(inst.x, placed_x[i]) + abs_diff(inst.y, placed_y[i]);
        out.wire_cost_q += static_cast<std::uint64_t>(distance) * 256;
        out.timing_cost_q += static_cast<std::uint64_t>(distance) * inst.criticality_q;
        out.boundary_cost_q += (placed_x[i] == page.xmin || placed_x[i] == page.xmax ||
                                placed_y[i] == page.ymin || placed_y[i] == page.ymax) ? 256 : 0;
        ++out.placed;
    }
    *metrics = out;
}
}
