#include <algorithm>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <stdexcept>
#include <vector>
using U=uint64_t; const U INF=std::numeric_limits<U>::max();
U add(U a,U b){if(b>=INF-a)throw std::runtime_error("overflow");return a+b;}
struct Query{U cid,sink;std::vector<U> path;};
struct Tree{std::map<U,U> delay,parent;U wire=0;};
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("input");std::ifstream f(argv[1]);auto read=[&](){U v;if(!(f>>v))throw std::runtime_error("truncated");return v;};
 if(read()!=2026100702)throw std::runtime_error("magic");U n=read(),m=read(),k=read(),penalty=read();if(!n||n>10000000||m>100000000||k>1000000)throw std::runtime_error("size");
 auto array=[&](U count){std::vector<U>a(count);for(auto&v:a)v=read();return a;};
 auto off=array(n+1),dest=array(m),weight=array(m),cap=array(n),initial=array(n),span=array(n);if(off[0]||off.back()!=m||!std::is_sorted(off.begin(),off.end()))throw std::runtime_error("offsets");for(U v:dest)if(v>=n)throw std::runtime_error("dest");
 std::vector<std::vector<Query>>nets(k);std::vector<U>sources(k),slot_src(m),occ(n,0);for(U u=0;u<n;++u)for(U s=off[u];s<off[u+1];++s)slot_src[s]=u;
 for(U a=0;a<k;++a){U count=read(),source=read();if(!count||count>10000000||source>=n)throw std::runtime_error("net");sources[a]=source;for(U j=0;j<count;++j){Query q;q.cid=read();q.sink=read();if(q.sink>=n)throw std::runtime_error("sink");U count=read();if(count>n)throw std::runtime_error("path length");q.path=array(count);nets[a].push_back(q);}}
 std::string extra;if(f>>extra)throw std::runtime_error("trailing");
 auto state=[&](U source,const std::vector<Query>&qs,U skip){Tree t;t.delay[source]=initial[source];t.wire=span[source];for(U j=0;j<qs.size();++j){if(j==skip)continue;U u=source,d=initial[source];for(U s:qs[j].path){if(s>=m||slot_src[s]!=u)throw std::runtime_error("arc");U v=dest[s];d=add(d,weight[s]);if(t.parent.count(v)&&t.parent[v]!=s)throw std::runtime_error("parents");if(t.delay.count(v)&&t.delay[v]!=d)throw std::runtime_error("prefix");if(!t.delay.count(v))t.wire=add(t.wire,span[v]);t.parent[v]=s;t.delay[v]=d;u=v;}if(u!=qs[j].sink)throw std::runtime_error("endpoint");}return t;};
 for(U a=0;a<k;++a){auto t=state(sources[a],nets[a],INF);for(auto [u,d]:t.delay)if(++occ[u]>cap[u])throw std::runtime_error("capacity");}
 for(U a=0;a<k;++a){U source=sources[a];auto &qs=nets[a];auto old=state(source,qs,INF);for(auto[u,d]:old.delay)--occ[u];std::cout<<"{\"index\":"<<a<<",\"attempts\":[";
  for(U j=0;j<qs.size();++j){auto retained=state(source,qs,j);std::vector<U>dist(n,INF),pred(n,INF);using Item=std::pair<U,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>>heap;
   for(auto[u,d]:retained.delay){dist[u]=d;heap.emplace(d,u);}U sink=qs[j].sink;
   while(!heap.empty()){auto[c,u]=heap.top();heap.pop();if(c!=dist[u])continue;if(u==sink)break;for(U s=off[u];s<off[u+1];++s){U v=dest[s];if(occ[v]>=cap[v]||retained.delay.count(v))continue;if(span[v]&&penalty>INF/span[v])throw std::runtime_error("penalty overflow");U next=add(add(c,weight[s]),penalty*span[v]);if(next<dist[v]){dist[v]=next;pred[v]=s;heap.emplace(next,v);}}}
   if(dist[sink]==INF)throw std::runtime_error("unreachable");std::vector<U>suffix,prefix;U u=sink;
   while(!retained.delay.count(u)){U s=pred[u];if(s==INF||suffix.size()>=n)throw std::runtime_error("predecessor");suffix.push_back(s);u=slot_src[s];}
   while(u!=source){U s=retained.parent.at(u);if(prefix.size()>=n)throw std::runtime_error("cycle");prefix.push_back(s);u=slot_src[s];}
   std::reverse(prefix.begin(),prefix.end());std::reverse(suffix.begin(),suffix.end());prefix.insert(prefix.end(),suffix.begin(),suffix.end());auto saved=qs[j].path;U olddelay=initial[source],trialdelay=initial[source];for(U s:saved)olddelay=add(olddelay,weight[s]);for(U s:prefix)trialdelay=add(trialdelay,weight[s]);U present=state(source,qs,INF).wire;qs[j].path=prefix;auto trial=state(source,qs,INF);bool accept=trialdelay<=olddelay&&trial.wire<=present&&(trialdelay<olddelay||trial.wire<present);if(!accept)qs[j].path=saved;
   if(j)std::cout<<",";std::cout<<"{\"connection_id\":"<<qs[j].cid<<",\"old_delay\":"<<olddelay<<",\"trial_delay\":"<<trialdelay<<",\"trial_wire\":"<<trial.wire<<",\"accepted\":"<<(accept?"true":"false")<<"}";
  }
  auto final=state(source,qs,INF);for(auto[u,d]:final.delay)if(++occ[u]>cap[u])throw std::runtime_error("final capacity");std::cout<<"],\"records\":[";
  for(U j=0;j<qs.size();++j){if(j)std::cout<<",";std::cout<<"{\"connection_id\":"<<qs[j].cid<<",\"delay\":"<<final.delay.at(qs[j].sink)<<",\"slots\":[";for(U p=0;p<qs[j].path.size();++p){if(p)std::cout<<",";std::cout<<qs[j].path[p];}std::cout<<"]}";}std::cout<<"],\"old_wire\":"<<old.wire<<",\"new_wire\":"<<final.wire<<"}\n";
 }
 return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<"\n";return 2;}}
