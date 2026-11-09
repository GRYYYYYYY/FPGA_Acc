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
    if(tile_count>MAX_TILES || edge_count>MAX_EDGES || dirty_count>MAX_DIRTY ||
       hop_limit>MAX_HOPS){out.invalid_batch=1; *metrics=out; return;}
    // Validate CSR before any mutation, including unreachable rows.
    for(std::uint32_t i=0;i<tile_count;++i){
        if(tiles[i].edge_begin>edge_count ||
           tiles[i].edge_count>edge_count-tiles[i].edge_begin){
            out.invalid_batch=1; *metrics=out; return;
        }
    }
    for(std::uint32_t e=0;e<edge_count;++e){
        if(edges[e].dst>=tile_count){out.invalid_batch=1; *metrics=out; return;}
    }
    std::uint32_t path[MAX_HOPS];
    for(std::uint32_t c=0;c<dirty_count;++c){
        const DirtyConnection connection=dirty[c];
        if(connection.source_tile>=tile_count || connection.sink_tile>=tile_count ||
           connection.flags!=0){
            ++out.invalid_connections; ++out.failed; continue;
        }
        std::uint32_t current=connection.source_tile, length=0;
        const Tile sink=tiles[connection.sink_tile];
        bool overflow=false;
        for(std::uint32_t hop=0;hop<hop_limit && current!=connection.sink_tile;++hop){
            const Tile t=tiles[current];
            const std::uint32_t current_distance=
                (t.x>sink.x?t.x-sink.x:sink.x-t.x)+
                (t.y>sink.y?t.y-sink.y:sink.y-t.y);
            std::uint32_t best=0xffffffffU;
            std::uint64_t best_score=~std::uint64_t{0};
            for(std::uint32_t j=0;j<t.edge_count;++j){
#ifdef __SYNTHESIS__
#pragma HLS PIPELINE II=1
#endif
                const std::uint32_t e=t.edge_begin+j;
                ++out.edge_visits;
                const EdgeTemplate edge=edges[e];
                if(edge.capacity==0) continue;
                const Tile dst=tiles[edge.dst];
                const std::uint32_t distance=
                    (dst.x>sink.x?dst.x-sink.x:sink.x-dst.x)+
                    (dst.y>sink.y?dst.y-sink.y:sink.y-dst.y);
                if(distance>=current_distance) continue;
                const std::uint64_t congestion=demand_q[e]/edge.capacity;
                const std::uint64_t score=static_cast<std::uint64_t>(distance)*256+
                    congestion*64+static_cast<std::uint64_t>(edge.segment_class)*8+
                    static_cast<std::uint64_t>(edge.pin_class)*4;
                if(score<best_score || (score==best_score && e<best)){
                    best=e; best_score=score;
                }
            }
            if(best==0xffffffffU) break;
            if(demand_q[best]>0xffffffffU-connection.demand_q){overflow=true; break;}
            path[length++]=best;
            current=edges[best].dst;
        }
        if(current!=connection.sink_tile){
            ++out.failed;
            if(overflow) ++out.overflow_rejections;
            continue;
        }
        ++out.completed;
        // Strict distance decrease prevents cycles and duplicate path edges.
        // Commit only after the complete candidate passes overflow checks.
        for(std::uint32_t i=0;i<length;++i){
            const std::uint32_t e=path[i];
            demand_q[e]+=connection.demand_q;
            ++out.updates;
            if(demand_q[e]>out.max_demand_q) out.max_demand_q=demand_q[e];
            if(demand_q[e]>static_cast<std::uint32_t>(edges[e].capacity)*256U)
                ++out.saturated;
        }
    }
    *metrics=out;
}
}
