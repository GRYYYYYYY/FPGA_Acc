#include "routecast.hpp"
namespace routecast {
extern "C" void routecast_kernel(const Tile tiles[MAX_TILES], const EdgeTemplate edges[MAX_EDGES],
 const DirtyConnection dirty[MAX_DIRTY], std::uint32_t demand_q[MAX_EDGES],
 std::uint32_t tile_count, std::uint32_t edge_count, std::uint32_t dirty_count,
 std::uint32_t hop_limit, SketchMetrics* metrics) {
#ifdef __SYNTHESIS__
#pragma HLS INTERFACE m_axi port=tiles bundle=gmem0
#pragma HLS INTERFACE m_axi port=edges bundle=gmem1
#pragma HLS INTERFACE m_axi port=dirty bundle=gmem2
#pragma HLS INTERFACE m_axi port=demand_q bundle=gmem3
#pragma HLS INTERFACE s_axilite port=tile_count bundle=control
#pragma HLS INTERFACE s_axilite port=edge_count bundle=control
#pragma HLS INTERFACE s_axilite port=dirty_count bundle=control
#pragma HLS INTERFACE s_axilite port=hop_limit bundle=control
#pragma HLS INTERFACE m_axi port=metrics bundle=gmem4
#pragma HLS INTERFACE s_axilite port=return bundle=control
#endif
    SketchMetrics out{};
    if(tile_count>MAX_TILES||edge_count>MAX_EDGES||dirty_count>MAX_DIRTY){*metrics=out;return;}
    for(std::uint32_t c=0;c<dirty_count;++c){
        std::uint32_t current=dirty[c].source_tile;
        for(std::uint32_t hop=0;hop<hop_limit && current!=dirty[c].sink_tile;++hop){
            if(current>=tile_count) break;
            const Tile t=tiles[current]; std::uint32_t best=0xffffffffU; std::uint64_t best_score=~std::uint64_t{0};
            for(std::uint32_t j=0;j<t.edge_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
                const std::uint32_t e=t.edge_begin+j; if(e>=edge_count) break; ++out.edge_visits;
                const EdgeTemplate edge=edges[e]; if(edge.dst>=tile_count) continue;
                const std::uint32_t dx=tiles[edge.dst].x>tiles[dirty[c].sink_tile].x?tiles[edge.dst].x-tiles[dirty[c].sink_tile].x:tiles[dirty[c].sink_tile].x-tiles[edge.dst].x;
                const std::uint32_t dy=tiles[edge.dst].y>tiles[dirty[c].sink_tile].y?tiles[edge.dst].y-tiles[dirty[c].sink_tile].y:tiles[dirty[c].sink_tile].y-tiles[edge.dst].y;
                const std::uint32_t current_distance=tiles[current].x>tiles[dirty[c].sink_tile].x?tiles[current].x-tiles[dirty[c].sink_tile].x:tiles[dirty[c].sink_tile].x-tiles[current].x;
                const std::uint32_t current_dy=tiles[current].y>tiles[dirty[c].sink_tile].y?tiles[current].y-tiles[dirty[c].sink_tile].y:tiles[dirty[c].sink_tile].y-tiles[current].y;
                if(dx+dy>=current_distance+current_dy) continue;
                const std::uint64_t congestion=demand_q[e]/(edge.capacity?edge.capacity:1);
                const std::uint64_t score=(dx+dy)*256+congestion*64+edge.segment_class*8+edge.pin_class*4;
                if(score<best_score||(score==best_score&&e<best)){best=e;best_score=score;}
            }
            if(best==0xffffffffU) break;
            demand_q[best]+=dirty[c].demand_q; ++out.updates;
            if(demand_q[best]>out.max_demand_q) out.max_demand_q=demand_q[best];
            if(demand_q[best]>static_cast<std::uint32_t>(edges[best].capacity)*256U) ++out.saturated;
            current=edges[best].dst;
        }
    }
    *metrics=out;
}
}
