#ifdef NDEBUG
#undef NDEBUG
#endif
#include "workspace_search.hpp"
#include <cassert>
extern "C" uint8_t routecast_workspace_csim(const routecast::PreparedSearchGraph&,uint64_t,const uint64_t*,uint64_t,uint64_t,routecast::SearchWorkspace&,routecast::SearchCounters&);
int main(){
 uint64_t rows[]={0,2,3,3},ids[]={0,1,2},dst[]={1,2,2},costs[]={1,9,1},caps[]={1,1,1};uint8_t types[]={0,4,1};
 routecast::PreparedSearchGraph g{rows,ids,dst,costs,caps,types,3,3};routecast::SearchLabel labels[3];uint8_t known[3],settled[3];uint64_t pos[3],heap[3],scratch[3],left[3],right[3];routecast::SearchWorkspace w{labels,known,settled,pos,heap,scratch,left,right,3,3,3};routecast::SearchCounters counters;uint64_t targets[]={2};
 auto run=[&](uint64_t budget){return static_cast<routecast::SearchTermination>(routecast_workspace_csim(g,0,targets,1,budget,w,counters));};
 assert(run(3)==routecast::SearchTermination::targets_complete);assert(labels[2].cost==2&&labels[2].parent==1&&labels[2].edge==2);assert(counters.settled==3&&counters.edge_visits==3);
 assert(run(0)==routecast::SearchTermination::work_budget);assert(!counters.settled);
 assert(run(1)==routecast::SearchTermination::work_budget);assert(counters.settled==1);
 w.frontier_capacity=0;assert(run(3)==routecast::SearchTermination::frontier_capacity);w.frontier_capacity=1;assert(run(3)==routecast::SearchTermination::frontier_capacity);w.frontier_capacity=3;
 costs[1]=UINT64_MAX;costs[2]=UINT64_MAX;assert(run(3)==routecast::SearchTermination::frontier_empty);costs[1]=9;costs[2]=1;
 costs[1]=1;w.path_capacity=0;assert(run(3)==routecast::SearchTermination::path_capacity);w.path_capacity=3;costs[1]=9;
 dst[0]=99;assert(run(3)==routecast::SearchTermination::invalid_input);dst[0]=1;
 uint64_t staged[3],staged_offsets[2],accepted[]={77,78,79},accepted_offsets[]={5,6},ec=3,tc=1;
 auto parent=[&](uint64_t r){return labels[r].parent;};auto edge=[&](uint64_t r){return labels[r].edge;};auto reached=[&](uint64_t r){return settled[r]!=0;};
 auto commit=[&](routecast::SearchTermination term,uint64_t capacity){return routecast::commit_paths(term,0,3,targets,1,parent,edge,reached,scratch,3,staged,3,staged_offsets,2,accepted,capacity,accepted_offsets,2,ec,tc);};
 assert(commit(run(1),3)==routecast::QueryStatus::work_budget);assert(accepted[0]==77&&accepted_offsets[0]==5&&ec==3&&tc==1);
 assert(commit(run(3),1)==routecast::QueryStatus::path_capacity);assert(accepted[0]==77&&accepted_offsets[0]==5&&ec==3&&tc==1);
 assert(commit(run(3),3)==routecast::QueryStatus::complete);assert(ec==2&&tc==1&&accepted[0]==0&&accepted[1]==2&&accepted_offsets[0]==0&&accepted_offsets[1]==2);
}
