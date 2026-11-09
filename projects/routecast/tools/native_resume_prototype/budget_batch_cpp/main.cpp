#include <algorithm>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <set>
#include <stdexcept>
#include <vector>
using U=uint64_t;const U INF=std::numeric_limits<U>::max();
U add(U a,U b){if(b>=INF-a)throw std::runtime_error("overflow");return a+b;}
struct Query{U cid,sink;std::vector<U> path;};
struct State{std::set<U> nodes;U wire=0;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("input");std::ifstream file(argv[1],std::ios::binary);
 auto read=[&](){unsigned char b[8];if(!file.read(reinterpret_cast<char*>(b),8))throw std::runtime_error("truncated");U v=0;for(unsigned i=0;i<8;++i)v|=U(b[i])<<(8*i);return v;};
 if(read()!=2026100705)throw std::runtime_error("magic");U n=read(),m=read(),k=read(),q=read(),budget=read();if(!n||n>10000000||m>100000000||k>1000000||q>k)throw std::runtime_error("size");
 auto array=[&](U size){std::vector<U> a(size);for(auto&v:a)v=read();return a;};
 auto off=array(n+1),dest=array(m),weight=array(m),cap=array(n),initial=array(n),span=array(n);if(off[0]||off.back()!=m||!std::is_sorted(off.begin(),off.end()))throw std::runtime_error("offsets");for(U v:dest)if(v>=n)throw std::runtime_error("dest");
 std::vector<U> source(k),slot_source(m),occ(n,0);for(U u=0;u<n;++u)for(U s=off[u];s<off[u+1];++s)slot_source[s]=u;
 std::vector<std::vector<Query>> nets(k);
 for(U i=0;i<k;++i){U count=read();source[i]=read();if(!count||count>10000000||source[i]>=n)throw std::runtime_error("net");for(U j=0;j<count;++j){Query x;x.cid=read();x.sink=read();if(x.sink>=n)throw std::runtime_error("sink");U length=read();if(length>n)throw std::runtime_error("path length");x.path=array(length);nets[i].push_back(x);}}
 auto order=array(q);std::set<U> unique;for(U i:order)if(i>=k||!unique.insert(i).second)throw std::runtime_error("selection");if(file.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing");
 auto state=[&](U src,const std::vector<Query>&queries){State result;result.nodes.insert(src);std::map<U,U> parents;
  for(auto&x:queries){U u=src;std::set<U> seen{src};for(U slot:x.path){if(slot>=m||slot_source[slot]!=u)throw std::runtime_error("arc");U v=dest[slot];if(!seen.insert(v).second)throw std::runtime_error("cycle");if(parents.count(v)&&parents[v]!=slot)throw std::runtime_error("parents");parents[v]=slot;result.nodes.insert(v);u=v;}if(u!=x.sink)throw std::runtime_error("endpoint");}
  for(U u:result.nodes)result.wire=add(result.wire,span[u]);return result;};
 std::vector<State> owners;U total=0;for(U i=0;i<k;++i){owners.push_back(state(source[i],nets[i]));total=add(total,owners.back().wire);for(U u:owners.back().nodes)if(++occ[u]>cap[u])throw std::runtime_error("capacity");}if(total>budget)throw std::runtime_error("initial budget");
 for(U index=0;index<q;++index){U i=order[index],src=source[i];auto&queries=nets[i];for(U u:owners[i].nodes)--occ[u];if(occ[src]>=cap[src])throw std::runtime_error("source capacity");
  std::vector<U> dist(n,INF),pred(n,INF);std::vector<bool> settled(n,false),wanted(n,false);U remaining=0;for(auto&x:queries){if(occ[x.sink]>=cap[x.sink])throw std::runtime_error("sink capacity");if(!wanted[x.sink]){wanted[x.sink]=true;++remaining;}}
  using Item=std::pair<U,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> heap;dist[src]=initial[src];heap.emplace(dist[src],src);
  while(!heap.empty()&&remaining){auto [cost,u]=heap.top();heap.pop();if(settled[u]||cost!=dist[u])continue;settled[u]=true;if(wanted[u]){wanted[u]=false;--remaining;}
   for(U s=off[u];s<off[u+1];++s){U v=dest[s];if(occ[v]>=cap[v])continue;U next=add(cost,weight[s]);if(next<dist[v]){dist[v]=next;pred[v]=s;heap.emplace(next,v);}}}
  if(remaining)throw std::runtime_error("unreachable");std::vector<Query> trials=queries;bool improves=false,nonincrease=true;
  for(auto&x:trials){U old=initial[src];for(U s:x.path)old=add(old,weight[s]);nonincrease=nonincrease&&dist[x.sink]<=old;improves=improves||dist[x.sink]<old;x.path.clear();U u=x.sink;while(u!=src){U slot=pred[u];if(slot==INF||x.path.size()>=n)throw std::runtime_error("predecessor");x.path.push_back(slot);u=slot_source[slot];}std::reverse(x.path.begin(),x.path.end());}
  auto trial=state(src,trials);for(U u:trial.nodes)if(occ[u]>=cap[u])throw std::runtime_error("trial capacity");U trialtotal=add(total-owners[i].wire,trial.wire);bool accepted=nonincrease&&improves&&trialtotal<=budget;
  std::cout<<"{\"index\":"<<index<<",\"net_index\":"<<i<<",\"old_wire\":"<<owners[i].wire<<",\"new_wire\":"<<trial.wire<<",\"previous_total_wire\":"<<total<<",\"trial_total_wire\":"<<trialtotal<<",\"accepted\":"<<(accepted?"true":"false")<<",\"records\":[";
  for(U j=0;j<trials.size();++j){if(j)std::cout<<",";auto&x=trials[j];std::cout<<"{\"connection_id\":"<<x.cid<<",\"minimum_integer\":"<<dist[x.sink]<<",\"slots\":[";for(U a=0;a<x.path.size();++a){if(a)std::cout<<",";std::cout<<x.path[a];}std::cout<<"]}";}std::cout<<"]}\n";
  if(accepted){queries=trials;owners[i]=trial;total=trialtotal;}for(U u:owners[i].nodes)if(++occ[u]>cap[u])throw std::runtime_error("commit capacity");
 }
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
