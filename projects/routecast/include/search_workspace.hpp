#pragma once
#include <cstdint>
#include "search_cost.hpp"
namespace routecast {
struct SearchLabel { SearchCost cost;uint64_t hops,parent,edge; };
// All regions must be disjoint caller-owned arrays. Capacities are element
// counts. Node IDs stored in these arrays are dense CSR ranks.
struct SearchWorkspace {
 SearchLabel* labels;uint8_t* known;uint8_t* settled;
 uint64_t* positions;uint64_t* frontier;
 uint64_t* scratch;uint64_t* left;uint64_t* right;
 uint64_t node_capacity,frontier_capacity,path_capacity;
};
enum class WorkspaceStatus { ok, node_capacity, invalid_storage };
inline WorkspaceStatus validate_workspace(const SearchWorkspace& w,uint64_t nodes){
 if(nodes>w.node_capacity)return WorkspaceStatus::node_capacity;
 if(nodes&&(!w.labels||!w.known||!w.settled||!w.positions))return WorkspaceStatus::invalid_storage;
 if(w.frontier_capacity&&!w.frontier)return WorkspaceStatus::invalid_storage;
 if(w.path_capacity&&(!w.scratch||!w.left||!w.right))return WorkspaceStatus::invalid_storage;
 return WorkspaceStatus::ok;
}
// Initialization touches work storage only. Accepted query results are separate.
inline WorkspaceStatus initialize_workspace(SearchWorkspace& w,uint64_t nodes){
 auto status=validate_workspace(w,nodes);if(status!=WorkspaceStatus::ok)return status;
 for(uint64_t i=0;i<nodes;++i){w.labels[i]={0,0,UINT64_MAX,UINT64_MAX};w.known[i]=0;w.settled[i]=0;w.positions[i]=UINT64_MAX;}
 return WorkspaceStatus::ok;
}
}
