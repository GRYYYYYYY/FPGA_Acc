#include <cstdint>
#include <vector>
#include <queue>
#include <algorithm>
#include <tuple>
#include <limits>
using U=unsigned __int128;
struct Label {uint64_t node,parent,slot;U cost,delay;bool live;};
struct Entry {U cost,delay;uint64_t node,id;};
struct Greater {bool operator()(const Entry&a,const Entry&b)const{return std::tie(a.cost,a.delay,a.node,a.id)>std::tie(b.cost,b.delay,b.node,b.id);}};
extern "C" int rc_query(uint64_t n,const uint64_t*rows,const uint64_t*dest,const uint64_t*edges,const uint64_t*costs,const uint64_t*capacities,const uint64_t*increments,const uint64_t*other,uint64_t source,uint64_t sink,uint64_t initial_lo,uint64_t initial_hi,uint64_t budget_lo,uint64_t budget_hi,uint64_t limit,uint64_t*out_path,uint64_t*out){
 // status: 0 FOUND, 1 UNREACHABLE, 2 LABEL_LIMIT, 3 ARITHMETIC_LIMIT, 4 INVALID_INPUT, 5 ALLOCATION_FAILURE.
 std::fill(out,out+8,0);if(source>=n||sink>=n||limit==0)return 4;
 try {
 U initial=(U(initial_hi)<<64)|initial_lo,budget=(U(budget_hi)<<64)|budget_lo;
 std::vector<Label> labels;std::vector<std::vector<uint64_t>>front(n);
 std::priority_queue<Entry,std::vector<Entry>,Greater>heap;
 if(initial>budget)return 1;
 labels.push_back({source,UINT64_MAX,0,0,initial,true});front[source].push_back(0);heap.push({0,initial,source,0});
 auto finish=[&](int status){out[0]=labels.size();return status;};
 while(!heap.empty()){
  auto e=heap.top();heap.pop();if(!labels[e.id].live)continue;++out[1];
  if(e.node==sink){std::vector<uint64_t>path;for(uint64_t id=e.id;labels[id].parent!=UINT64_MAX;id=labels[id].parent)path.push_back(edges[labels[id].slot]);std::reverse(path.begin(),path.end());std::copy(path.begin(),path.end(),out_path);out[3]=path.size();out[4]=uint64_t(e.cost);out[5]=uint64_t(e.cost>>64);out[6]=uint64_t(e.delay);out[7]=uint64_t(e.delay>>64);return finish(0);}
  for(uint64_t i=rows[e.node];i<rows[e.node+1];++i){
   ++out[2];uint64_t v=dest[i];if(v>=n)return finish(4);if(costs[i]==UINT64_MAX||capacities[v]==0)continue;
   U weight=U(costs[i])*(U(other[v])+1);if(~U(0)-e.cost<weight||~U(0)-e.delay<increments[i])return finish(3);
   U nc=e.cost+weight,nd=e.delay+increments[i];if(nd>budget)continue;
   auto&old=front[v];bool dominated=false;for(auto id:old)if(labels[id].cost<=nc&&labels[id].delay<=nd){dominated=true;break;}if(dominated)continue;
   if(labels.size()>=limit)return finish(2);
   std::vector<uint64_t>keep;for(auto id:old){if(nc<=labels[id].cost&&nd<=labels[id].delay)labels[id].live=false;else keep.push_back(id);}
   uint64_t id=labels.size();labels.push_back({v,e.id,i,nc,nd,true});keep.push_back(id);old.swap(keep);heap.push({nc,nd,v,id});
  }
 }
 return finish(1);
 }catch(...){return 5;}
}
