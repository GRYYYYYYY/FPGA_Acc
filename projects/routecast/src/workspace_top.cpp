#include "workspace_search.hpp"
// C-simulation entry for the complete caller-workspace semantic core.
// Nested pointer structs are a software harness, not the final AXI ABI.
extern "C" uint8_t routecast_workspace_csim(
 const routecast::PreparedSearchGraph& graph,uint64_t source,
 const uint64_t* targets,uint64_t count,uint64_t budget,
 routecast::SearchWorkspace& workspace,routecast::SearchCounters& counters){
 return static_cast<uint8_t>(routecast::workspace_search(graph,source,targets,count,budget,workspace,counters));
}
