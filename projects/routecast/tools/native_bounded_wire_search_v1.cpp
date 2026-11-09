#include <cstdint>
#include <vector>
#include <queue>
#include <tuple>
#include <limits>
#include <algorithm>
#include <stdexcept>
using U=uint64_t;
struct Context {U n,m;const U *row,*dest,*eid,*sw,*inc,*cap,*length;std::vector<U> path;};
struct Result {U status,cost,delay,created,expanded,examined,path_size;};
struct Label {U node,cost,delay,parent,slot;bool alive;};
extern "C" void* rc_create(U n,U m,const U* row,const U* dest,const U* eid,const U* sw,const U* inc,const U* cap,const U* length){
 try {if(!n||row[0]!=0||row[n]!=m)return nullptr;for(U u=0;u<n;u++)if(row[u]>row[u+1])return nullptr;for(U i=0;i<m;i++)if(dest[i]>=n||sw[i]==std::numeric_limits<U>::max())return nullptr;return new Context{n,m,row,dest,eid,sw,inc,cap,length,{}};}catch(...){return nullptr;}
}
extern "C" void rc_destroy(void* ptr){delete static_cast<Context*>(ptr);}
extern "C" int rc_query(void* ptr,U source,U sink,U initial,U budget,U bound,U max_labels,const U* outside,const uint8_t* kept,const U* parent_source,const U* parent_switch,Result* out){
 try {
  auto& c=*static_cast<Context*>(ptr);if(source>=c.n||sink>=c.n||!max_labels)return -1;c.path.clear();*out=Result{1,0,0,0,0,0,0};
  if(initial>budget||!bound)return 0;
  const U none=std::numeric_limits<U>::max();std::vector<Label> labels;std::vector<std::vector<U>> front(c.n);
  using Key=std::tuple<U,U,U,U>;std::priority_queue<Key,std::vector<Key>,std::greater<Key>> queue;
  labels.push_back({source,0,initial,none,none,true});front[source].push_back(0);queue.emplace(0,initial,source,0);
  auto finish=[&](U status){out->status=status;out->created=labels.size();out->path_size=c.path.size();return 0;};
  while(!queue.empty()){
   auto [objective,delay,node,lid]=queue.top();queue.pop();if(!labels[lid].alive)continue;out->expanded++;
   if(node==sink){
    out->cost=objective;out->delay=delay;U cursor=lid;
    while(labels[cursor].parent!=none){c.path.push_back(c.eid[labels[cursor].slot]);cursor=labels[cursor].parent;}
    std::reverse(c.path.begin(),c.path.end());return finish(0);
   }
   for(U i=c.row[node];i<c.row[node+1];i++){
    out->examined++;U dest=c.dest[i];if(outside[dest]>=c.cap[dest])continue;
    if(parent_source[dest]&&(parent_source[dest]!=node+1||parent_switch[dest]!=c.sw[i]+1))continue;
    U w=kept[dest]?0:c.length[dest];
    // All queued labels satisfy delay<=budget and objective<bound. These
    // comparisons exactly implement both integer bounds before adding.
    if(c.inc[i]>budget-delay||w>=bound-objective)continue;
    U nd=delay+c.inc[i],nc=objective+w;auto& old=front[dest];bool dominated=false;
    for(U x:old)if(labels[x].cost<=nc&&labels[x].delay<=nd){dominated=true;break;}
    if(dominated)continue;
    if(labels.size()>=max_labels)return finish(2);
    std::vector<U> keep;keep.reserve(old.size()+1);
    for(U x:old){if(nc<=labels[x].cost&&nd<=labels[x].delay)labels[x].alive=false;else keep.push_back(x);}
    U next=labels.size();labels.push_back({dest,nc,nd,lid,i,true});keep.push_back(next);old.swap(keep);queue.emplace(nc,nd,dest,next);
   }
  }
  return finish(1);
 }catch(...){return -2;}
}
extern "C" int rc_copy_path(void* ptr,U* output,U size){auto& c=*static_cast<Context*>(ptr);if(size!=c.path.size())return -1;std::copy(c.path.begin(),c.path.end(),output);return 0;}
