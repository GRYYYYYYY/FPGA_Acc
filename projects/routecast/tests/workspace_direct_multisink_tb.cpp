#ifdef NDEBUG
#undef NDEBUG
#endif
#include "workspace_direct.hpp"
#include <cassert>
int main(){
 // Parallel zero-cost edges, zero cycle, equal-cost detours, shared multi-sink trunk.
 uint64_t rows[]={0,3,5,7,9,9,9};
 uint64_t ids[]={0,1,2,3,4,5,8,6,7};
 uint64_t dst[]={1,1,2,2,3,3,1,4,5};
 uint64_t costs[]={0,0,0,0,1,1,0,0,0};
 uint64_t caps[]={1,1,1,1,1,1};uint8_t types[]={0,5,4,3,1,1};uint64_t targets[]={4,5};
 routecast::SearchLabel labels[6]{};uint8_t known[6]{},settled[6]{};uint64_t positions[6]{},frontier[6]{},scratch[6]{},left[6]{},right[6]{},stage[6]{},stage_offsets[3]{},accepted[6]={91,92,93,94,95,96},offsets[3]={9,9,9};uint64_t edge_count=6,target_count=2;routecast::SearchCounters counters{};
 auto run=[&](uint64_t budget,uint64_t stagecap,uint64_t outputcap){return routecast::QueryStatus(routecast_workspace_direct(rows,ids,dst,costs,caps,types,6,9,0,targets,2,budget,1,labels,known,settled,positions,frontier,scratch,left,right,6,6,6,stage,stagecap,stage_offsets,3,accepted,outputcap,offsets,3,edge_count,target_count,counters));};
 // Budget reaches first SINK but leaves second incomplete: preserve entire old net.
 assert(run(5,6,6)==routecast::QueryStatus::work_budget);assert(accepted[0]==91&&accepted[5]==96&&offsets[0]==9&&edge_count==6);
 assert(run(6,5,6)==routecast::QueryStatus::path_capacity);assert(accepted[0]==91&&accepted[5]==96&&offsets[0]==9);
 assert(run(6,6,5)==routecast::QueryStatus::path_capacity);assert(accepted[0]==91&&accepted[5]==96&&offsets[0]==9);
 assert(run(6,6,6)==routecast::QueryStatus::complete);uint64_t expected[]={0,4,6,0,4,7};for(unsigned i=0;i<6;++i)assert(accepted[i]==expected[i]);assert(offsets[0]==0&&offsets[1]==3&&offsets[2]==6&&edge_count==6&&target_count==2);
 assert(counters.settled==6&&counters.edge_visits==9);
 // Disable second SINK arc; completed first path does not replace the previous net.
 costs[8]=UINT64_MAX;assert(run(6,6,6)==routecast::QueryStatus::unreachable);for(unsigned i=0;i<6;++i)assert(accepted[i]==expected[i]);assert(offsets[1]==3&&edge_count==6);
}
