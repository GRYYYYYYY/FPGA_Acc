#ifdef NDEBUG
#undef NDEBUG
#endif
#include "search_workspace.hpp"
#include <cassert>
int main(){
 routecast::SearchLabel labels[3];uint8_t known[3]={1,1,1},settled[3]={1,1,1};uint64_t positions[3],frontier[2]={91,92},scratch[2],left[2],right[2];
 routecast::SearchWorkspace w{labels,known,settled,positions,frontier,scratch,left,right,3,2,2};
 assert(routecast::validate_workspace(w,4)==routecast::WorkspaceStatus::node_capacity);
 assert(routecast::validate_workspace(w,3)==routecast::WorkspaceStatus::ok);
 auto bad=w;bad.labels=nullptr;assert(routecast::validate_workspace(bad,3)==routecast::WorkspaceStatus::invalid_storage);
 bad=w;bad.frontier=nullptr;assert(routecast::validate_workspace(bad,3)==routecast::WorkspaceStatus::invalid_storage);
 bad=w;bad.right=nullptr;assert(routecast::validate_workspace(bad,3)==routecast::WorkspaceStatus::invalid_storage);
 assert(routecast::initialize_workspace(w,4)==routecast::WorkspaceStatus::node_capacity);assert(known[0]==1&&settled[0]==1);
 assert(routecast::initialize_workspace(w,3)==routecast::WorkspaceStatus::ok);
 for(unsigned i=0;i<3;++i){assert(labels[i].cost==0&&labels[i].hops==0&&labels[i].parent==UINT64_MAX&&labels[i].edge==UINT64_MAX);assert(!known[i]&&!settled[i]&&positions[i]==UINT64_MAX);}
 assert(frontier[0]==91&&frontier[1]==92);
 routecast::SearchWorkspace empty{};assert(routecast::validate_workspace(empty,0)==routecast::WorkspaceStatus::ok);
}
