#include <cstdint>
#include <vector>
#include <queue>
#include <functional>
#include <limits>
using U=uint64_t;using W=unsigned __int128;
struct BranchWorkspace {
 U n;std::vector<W> cost;std::vector<U> raw,pn,pe,touched;
 std::vector<uint8_t> done;
 explicit BranchWorkspace(U count):n(count),cost(count,W(1)<<120),raw(count),pn(count),pe(count),done(count,0){}
};
extern "C" void* marginal_create(U n){try{return n?new BranchWorkspace(n):nullptr;}catch(...){return nullptr;}}
extern "C" void marginal_destroy(void* p){delete static_cast<BranchWorkspace*>(p);}
// Output only the new extension in forward order. cost is returned as two words.
extern "C" int marginal_branch(void* handle,U sink,U weight,U seeds_count,const U* seeds,const U* prefixes,const U* row,const U* dest,const U* inc,const U* cap,const U* price,const uint8_t* owned,U* edge_output,U* count,U* attachment,U* delay,U* cost_low,U* cost_high){
 try {
  auto* w=static_cast<BranchWorkspace*>(handle);if(!w||sink>=w->n||!seeds_count)return -1;
  const W infinity=W(1)<<120;const U none=std::numeric_limits<U>::max();
  *count=0;
  for(U n:w->touched){w->cost[n]=infinity;w->done[n]=0;}w->touched.clear();
  using Item=std::pair<W,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> q;
  for(U i=0;i<seeds_count;i++){
   U n=seeds[i];if(n>=w->n||!owned[n]||w->cost[n]!=infinity)return -1;
   w->touched.push_back(n);w->cost[n]=0;w->raw[n]=prefixes[i];q.push({0,n});
  }
  bool found=false;
  while(!q.empty()){
   auto [value,u]=q.top();q.pop();if(value!=w->cost[u]||w->done[u])continue;
   w->done[u]=1;if(u==sink){found=true;break;}
   for(U e=row[u];e<row[u+1];e++){
    U v=dest[e];if(v>=w->n)return -1;if(!cap[v]||owned[v])continue;
    W next=value+inc[e]+W(weight)*price[v];if(next>=infinity)return -2;
    if(next<w->cost[v]){
     W next_raw=W(w->raw[u])+inc[e];if(next_raw>=none)return -2;
     if(w->cost[v]==infinity)w->touched.push_back(v);
     w->cost[v]=next;w->raw[v]=U(next_raw);w->pn[v]=u;w->pe[v]=e;q.push({next,v});
    }
   }
  }
  if(!found)return 1;
  U u=sink;std::vector<U> path;
  while(!owned[u]){if(path.size()>=w->n)return -3;path.push_back(w->pe[u]);u=w->pn[u];}
  *attachment=u;*delay=w->raw[sink];*count=path.size();*cost_low=U(w->cost[sink]);*cost_high=U(w->cost[sink]>>64);
  for(U i=0;i<path.size();i++)edge_output[i]=path[path.size()-1-i];
  return 0;
 }catch(...){return -3;}
}
