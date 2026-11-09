// Reuse the certified monotone radix heap, including its node-ID tie order.
#include "tree_workspace_radix_stats_v4.cpp"
#include <unordered_map>
struct Bidi {
 U n;
 std::vector<U> row,dest,inc,cap,rr,rd,re;
 std::vector<Wide> distance[2];
 std::vector<U> parent[2],edge[2],touched[2];
 std::vector<uint8_t> done[2];
 ReusedHeap queue[2];
 const Wide inf=Wide(1)<<120;
 Bidi(U size,const U* r,const U* d,const U* i,const U* c):n(size),row(r,r+size+1),dest(d,d+r[size]),inc(i,i+r[size]),cap(c,c+size),rr(size+1,0){
  for(U u=0;u<n;++u)for(U e=row[u];e<row[u+1];++e)++rr[dest[e]+1];
  for(U u=0;u<n;++u)rr[u+1]+=rr[u];
  rd.resize(dest.size());re.resize(dest.size());auto next=rr;
  for(U u=0;u<n;++u)for(U e=row[u];e<row[u+1];++e){U p=next[dest[e]]++;rd[p]=u;re[p]=e;}
  for(int s=0;s<2;++s){distance[s].assign(n,inf);parent[s].resize(n);edge[s].resize(n);done[s].assign(n,0);}
 }
};
extern "C" void* rc_bidi_create(U n,const U* row,const U* dest,const U* inc,const U* cap){
 try{
  if(!n||!row||!dest||!inc||!cap||row[0])return nullptr;
  for(U u=0;u<n;++u){if(row[u]>row[u+1])return nullptr;for(U e=row[u];e<row[u+1];++e)if(dest[e]>=n)return nullptr;}
  return new Bidi(n,row,dest,inc,cap);
 }catch(...){return nullptr;}
}
extern "C" void rc_bidi_destroy(void* p){delete static_cast<Bidi*>(p);}
// Success commits outputs. Unreachable=1 commits only count=0. Negative
// status invalidates this query; output buffers are never accepted by bridge.
extern "C" int rc_bidi_search(void* handle,U src,U sink,U initial,U weight,const U* price,U* slots,U limit,U* count,U* raw,U* low,U* high,U* stats){
 try{
  auto* w=static_cast<Bidi*>(handle);
  if(!w||src>=w->n||sink>=w->n||!w->cap[src]||!w->cap[sink]||!price||!slots||!count||!raw||!low||!high||!stats||limit<w->n)return -1;
  U work[4]={};
  for(int s=0;s<2;++s){
   for(U u:w->touched[s]){w->distance[s][u]=w->inf;w->done[s][u]=0;}
   w->touched[s].clear();w->queue[s].clear();
  }
  auto set=[&](int s,U u,Wide value){if(w->distance[s][u]==w->inf)w->touched[s].push_back(u);w->distance[s][u]=value;};
  set(0,src,0);set(1,sink,0);w->queue[0].push({0,src});w->queue[1].push({0,sink});
  Wide best=w->inf;U meet=w->n;
  auto bound=[&](U u){if(w->distance[0][u]!=w->inf&&w->distance[1][u]!=w->inf){Wide sum=w->distance[0][u]+w->distance[1][u];if(sum<best){best=sum;meet=u;}}};
  bound(src);
  while(true){
   for(int s=0;s<2;++s){auto& q=w->queue[s];while(!q.empty()){auto item=q.top();if(item.first==w->distance[s][item.second]&&!w->done[s][item.second])break;q.pop();}}
   if(w->queue[0].empty()||w->queue[1].empty())break;
   auto a=w->queue[0].top(),b=w->queue[1].top();
   if(best!=w->inf&&a.first+b.first>=best)break;
   int s=b<a;auto [cost,u]=w->queue[s].top();w->queue[s].pop();w->done[s][u]=1;++work[s+2];
   U start=s?w->rr[u]:w->row[u],end=s?w->rr[u+1]:w->row[u+1];
   for(U p=start;p<end;++p){
    ++work[s];U v=s?w->rd[p]:w->dest[p],e=s?w->re[p]:p;
    if(!w->cap[v])continue;
    U destination=s?u:v;
    Wide value=cost+w->inc[e]+Wide(weight)*price[destination];
    if(value>=w->inf)return -2;
    if(value<w->distance[s][v]){set(s,v,value);w->parent[s][v]=u;w->edge[s][v]=e;w->queue[s].push({value,v});bound(v);}
   }
  }
  if(meet==w->n){*count=0;std::copy(work,work+4,stats);return 1;}
  std::vector<U> path;U u=meet;
  while(u!=src){if(path.size()>=w->n)return -3;path.push_back(w->edge[0][u]);u=w->parent[0][u];}
  std::reverse(path.begin(),path.end());u=meet;U steps=0;
  while(u!=sink){if(++steps>w->n)return -3;path.push_back(w->edge[1][u]);u=w->parent[1][u];}
  std::vector<U> nodes{src},result;std::unordered_map<U,U> position;position[src]=0;
  for(U e:path){
   u=nodes.back();if(e<w->row[u]||e>=w->row[u+1])return -3;
   U v=w->dest[e];auto found=position.find(v);
   if(found==position.end()){position[v]=nodes.size();nodes.push_back(v);result.push_back(e);}
   else{
    U k=found->second;Wide removed=w->inc[e]+Wide(weight)*price[v];
    for(U j=k;j<result.size();++j){U x=result[j];removed+=w->inc[x]+Wide(weight)*price[w->dest[x]];}
    if(removed)return -3;
    for(U j=k+1;j<nodes.size();++j)position.erase(nodes[j]);
    nodes.resize(k+1);result.resize(k);
   }
  }
  Wide original=initial,objective=initial;
  for(U e:result){original+=w->inc[e];objective+=w->inc[e]+Wide(weight)*price[w->dest[e]];}
  if(nodes.back()!=sink||objective!=Wide(initial)+best)return -3;
  if(original>=std::numeric_limits<U>::max()||objective>=w->inf)return -2;
  std::copy(result.begin(),result.end(),slots);*count=result.size();*raw=U(original);*low=U(objective);*high=U(objective>>64);std::copy(work,work+4,stats);return 0;
 }catch(...){return -3;}
}
