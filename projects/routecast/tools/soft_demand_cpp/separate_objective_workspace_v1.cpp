#include <cstdint>
#include <vector>
#include <queue>
#include <functional>
#include <limits>
#include <algorithm>
using U=uint64_t;using Wide=unsigned __int128;
extern "C" int rc_tree(U n,U src,U initial,U weight,const U* targets,U count,const U* row,const U* dest,const U* inc,const U* objective,const U* cap,const U* price,U* raw,U* pn,U* pe,uint8_t* settled){
 try {
  if(!n||src>=n)return -1;
  const U none=std::numeric_limits<U>::max();const Wide infinity=Wide(1)<<120;
  std::vector<Wide> d(n,infinity);std::vector<uint8_t> wanted(n,0);U remaining=0;
  for(U i=0;i<count;i++){if(targets[i]>=n)return -1;if(!wanted[targets[i]]){wanted[targets[i]]=1;remaining++;}}
  std::fill(raw,raw+n,none);std::fill(pn,pn+n,none);std::fill(pe,pe+n,none);std::fill(settled,settled+n,0);
  using Item=std::pair<Wide,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
  d[src]=initial;raw[src]=initial;queue.push({initial,src});
  while(!queue.empty()&&remaining){
   auto [cost,u]=queue.top();queue.pop();if(cost!=d[u])continue;
   if(!settled[u]){settled[u]=1;if(wanted[u])remaining--;}
   for(U e=row[u];e<row[u+1];e++){
    U v=dest[e];if(v>=n)return -1;if(!cap[v])continue;
    Wide next=cost+objective[e]+Wide(weight)*price[v];if(next>=infinity)return -2;
    if(next<d[v]){Wide nextRaw=Wide(raw[u])+inc[e];if(nextRaw>=none)return -2;d[v]=next;raw[v]=U(nextRaw);pn[v]=u;pe[v]=e;queue.push({next,v});}
   }
  }
  return 0;
 }catch(...){return -3;}
}

struct Workspace {
 U n;bool primed=false;U *owner_raw=nullptr,*owner_pn=nullptr,*owner_pe=nullptr;uint8_t* owner_settled=nullptr;
 std::vector<Wide> d;std::vector<uint8_t> wanted;std::vector<U> touched,targets;
 explicit Workspace(U count):n(count),d(count,Wide(1)<<120),wanted(count,0){}
};
extern "C" void* rc_workspace_create(U n){try {if(!n)return nullptr;return new Workspace(n);}catch(...){return nullptr;}}
extern "C" void rc_workspace_destroy(void* p){delete static_cast<Workspace*>(p);}
extern "C" int rc_tree_workspace(void* handle,U n,U src,U initial,U weight,const U* targets,U count,const U* row,const U* dest,const U* inc,const U* objective,const U* cap,const U* price,U* raw,U* pn,U* pe,uint8_t* settled){
 try {
  auto* w=static_cast<Workspace*>(handle);if(!w||!n||w->n!=n||src>=n)return -1;
  for(U i=0;i<count;i++)if(targets[i]>=n)return -1;
  if(w->primed&&(w->owner_raw!=raw||w->owner_pn!=pn||w->owner_pe!=pe||w->owner_settled!=settled))return -1;
  const U none=std::numeric_limits<U>::max();const Wide infinity=Wide(1)<<120;
  if(!w->primed||w->touched.size()>n/4){
   std::fill(w->d.begin(),w->d.end(),infinity);std::fill(raw,raw+n,none);std::fill(pn,pn+n,none);std::fill(pe,pe+n,none);std::fill(settled,settled+n,0);
  }else for(U node:w->touched){w->d[node]=infinity;raw[node]=pn[node]=pe[node]=none;settled[node]=0;}
  w->owner_raw=raw;w->owner_pn=pn;w->owner_pe=pe;w->owner_settled=settled;w->primed=true;w->touched.clear();
  for(U node:w->targets)w->wanted[node]=0;w->targets.clear();U remaining=0;
  for(U i=0;i<count;i++)if(!w->wanted[targets[i]]){w->targets.push_back(targets[i]);w->wanted[targets[i]]=1;remaining++;}
  using Item=std::pair<Wide,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> queue;
  w->touched.push_back(src);w->d[src]=initial;raw[src]=initial;queue.push({initial,src});
  while(!queue.empty()&&remaining){
   auto [cost,u]=queue.top();queue.pop();if(cost!=w->d[u])continue;
   if(!settled[u]){settled[u]=1;if(w->wanted[u])remaining--;}
   for(U e=row[u];e<row[u+1];e++){
    U v=dest[e];if(v>=n)return -1;if(!cap[v])continue;
    Wide next=cost+objective[e]+Wide(weight)*price[v];if(next>=infinity)return -2;
    if(next<w->d[v]){Wide nextRaw=Wide(raw[u])+inc[e];if(nextRaw>=none)return -2;if(w->d[v]==infinity)w->touched.push_back(v);w->d[v]=next;raw[v]=U(nextRaw);pn[v]=u;pe[v]=e;queue.push({next,v});}
   }
  }
  return 0;
 }catch(...){return -3;}
}
