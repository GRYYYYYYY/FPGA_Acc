#pragma once
#include "accelerated_pathfinder.hpp"

namespace dieroute {
// Edge IDs index the frozen CSR edge array. Native PIP ID/direction is a
// separate immutable per-edge sidecar; never infer it from a node pair.
struct EdgeBatchResult {
    persistroute::KernelBatchResult batch;
    std::vector<std::vector<std::uint32_t>> edge_paths; // aligned with candidates
};
struct EdgeTreeEntry { std::uint32_t net_id, parent, child, edge; };
inline bool valid_edge_path(const std::vector<persistroute::Node>& nodes,
    const std::vector<persistroute::Edge>& edges, std::uint32_t attachment,
    const std::vector<std::uint32_t>& path, const std::vector<std::uint32_t>& edge_path) {
    if(attachment>=nodes.size() || path.size()!=edge_path.size())return false;
    auto parent=attachment;
    for(std::size_t i=0;i<path.size();++i){
        const auto id=edge_path[i];const auto& node=nodes[parent];
        if(path[i]>=nodes.size() || id>=edges.size() || id<node.edge_begin ||
           std::uint64_t(id)>=std::uint64_t(node.edge_begin)+node.edge_count || edges[id].dst!=path[i])return false;
        parent=path[i];
    }
    return true;
}
} // namespace dieroute
