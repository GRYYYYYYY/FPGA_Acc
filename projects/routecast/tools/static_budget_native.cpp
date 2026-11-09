#include <cstdint>
#include <vector>
#include <queue>
#include <unordered_set>
#include <algorithm>
using U=unsigned __int128;
struct Graph { uint64_t n,epoch=0; std::vector<uint64_t> rows,dest,inc,caps,seen,settled;std::vector<U> dist; };
extern "C" int floor_create(uint64_t n,uint64_t m,const uint64_t*r,const uint64_t*d,const uint64_t*i,const uint64_t*c,void**out){
 if(!out||!n||!r||!c||(!d&&m)||(!i&&m)||r[0]||r[n]!=m)return 1;
 for(uint64_t k=0;k<n;k++)if(r[k]>r[k+1])return 1;
 for(uint64_t k=0;k<m;k++)if(d[k]>=n)return 1;
 try{auto*g=new Graph;g->n=n;try{g->rows.assign(r,r+n+1);g->dest.assign(d,d+m);g->inc.assign(i,i+m);g->caps.assign(c,c+n);g->seen.resize(n);g->settled.resize(n);g->dist.resize(n);}catch(...){delete g;throw;}*out=g;return 0;}catch(...){return 2;}
}
extern "C" void floor_destroy(void*p){delete static_cast<Graph*>(p);}
extern "C" int floor_query(void*p,uint64_t source,uint64_t il,uint64_t ih,uint64_t bl,uint64_t bh,uint64_t count,const uint64_t*targets,uint64_t*lo,uint64_t*hi,uint64_t*found,uint64_t*stats){
 auto*g=static_cast<Graph*>(p);if(!g||source>=g->n||!stats||(count&&(!targets||!lo||!hi||!found)))return 1;
 for(uint64_t k=0;k<count;k++)if(targets[k]>=g->n)return 1;
 try{
  if(++g->epoch==0){std::fill(g->seen.begin(),g->seen.end(),0);std::fill(g->settled.begin(),g->settled.end(),0);g->epoch=1;}
  uint64_t ep=g->epoch,settled=0,examined=0;U initial=(U(ih)<<64)|il,budget=(U(bh)<<64)|bl;
  using Item=std::pair<U,uint64_t>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>>q;std::unordered_set<uint64_t>remaining;
  for(uint64_t k=0;k<count;k++)remaining.insert(targets[k]);
  if(g->caps[source]&&initial<=budget){g->seen[source]=ep;g->dist[source]=initial;q.push({initial,source});}
  while(!q.empty()&&!remaining.empty()){
   auto [value,node]=q.top();q.pop();if(g->settled[node]==ep||g->seen[node]!=ep||value!=g->dist[node])continue;
   g->settled[node]=ep;++settled;remaining.erase(node);
   for(uint64_t k=g->rows[node];k<g->rows[node+1];k++){
    ++examined;uint64_t dst=g->dest[k];if(!g->caps[dst]||g->settled[dst]==ep||U(g->inc[k])>budget-value)continue;
    U next=value+g->inc[k];if(g->seen[dst]!=ep||next<g->dist[dst]){g->seen[dst]=ep;g->dist[dst]=next;q.push({next,dst});}
   }
  }
  for(uint64_t k=0;k<count;k++){bool yes=g->settled[targets[k]]==ep;found[k]=yes;U v=yes?g->dist[targets[k]]:0;lo[k]=uint64_t(v);hi[k]=uint64_t(v>>64);}
  stats[0]=settled;stats[1]=examined;return 0;
 }catch(...){return 2;}
}
