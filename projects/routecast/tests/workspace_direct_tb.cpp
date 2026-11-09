#ifdef NDEBUG
#undef NDEBUG
#endif
#include "workspace_direct.hpp"
#include <cassert>
int main(){
 uint64_t rows[]={0,1,2,2},edges[]={0,1},dst[]={1,2},cost[]={UINT64_MAX-1,UINT64_MAX-1},caps[]={1,1,1},target[]={2};uint8_t types[]={0,4,1};routecast::SearchLabel labels[3];uint8_t known[3],settled[3];uint64_t pos[3],heap[3],scratch[3],left[3],right[3],stage[3],stageoff[2],accepted[]={77,78,79},off[]={5,6},ec=3,tc=1;routecast::SearchCounters counters;
 auto run=[&](uint64_t budget,uint8_t verified,uint64_t outputcap){return routecast::QueryStatus(routecast_workspace_direct(rows,edges,dst,cost,caps,types,3,2,0,target,1,budget,verified,labels,known,settled,pos,heap,scratch,left,right,3,3,3,stage,3,stageoff,2,accepted,outputcap,off,2,ec,tc,counters));};
 assert(run(3,0,3)==routecast::QueryStatus::unsupported_context);assert(accepted[0]==77&&ec==3&&off[0]==5);
 assert(run(1,1,3)==routecast::QueryStatus::work_budget);assert(accepted[0]==77&&ec==3&&off[0]==5);
 assert(run(3,1,1)==routecast::QueryStatus::path_capacity);assert(accepted[0]==77&&ec==3&&off[0]==5);
 assert(run(3,1,3)==routecast::QueryStatus::complete);assert(ec==2&&tc==1&&accepted[0]==0&&accepted[1]==1&&off[0]==0&&off[1]==2);assert(labels[2].cost.high==1);
}
