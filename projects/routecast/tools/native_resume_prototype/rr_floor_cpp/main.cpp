#include <algorithm>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <queue>
#include <stdexcept>
#include <tuple>
#include <vector>
using U=uint64_t;
U read(std::ifstream& f){ U v; if(!f.read(reinterpret_cast<char*>(&v),8))throw std::runtime_error("truncated input");return v; }
std::vector<U> values(std::ifstream& f,U n){std::vector<U> a(n);for(auto& v:a)v=read(f);return a;}
int main(int argc,char** argv){try{
 if(argc!=2)throw std::runtime_error("expected input file");std::ifstream f(argv[1],std::ios::binary);if(!f)throw std::runtime_error("open input");
 if(read(f)!=0x5243464c4f4f5231ULL)throw std::runtime_error("format");U n=read(f),m=read(f),q=read(f);if(!n||n>10000000||m>100000000||q>10000000)throw std::runtime_error("size");
 auto offsets=values(f,n+1),dest=values(f,m),weight=values(f,m),capacity=values(f,n),initial=values(f,n);
 if(offsets.front()!=0||offsets.back()!=m||!std::is_sorted(offsets.begin(),offsets.end()))throw std::runtime_error("offsets");for(U v:dest)if(v>=n)throw std::runtime_error("dest");
 std::vector<std::tuple<U,U,U>> queries;std::map<U,std::vector<U>> groups;
 for(U i=0;i<q;++i){U cid=read(f),src=read(f),sink=read(f);if(src>=n||sink>=n||!capacity[src]||!capacity[sink])throw std::runtime_error("endpoint");queries.emplace_back(cid,src,sink);groups[src].push_back(i);}
 if(f.peek()!=std::char_traits<char>::eof())throw std::runtime_error("trailing data");
 const U inf=std::numeric_limits<U>::max();std::vector<U> slot_source(m);for(U u=0;u<n;++u)for(U s=offsets[u];s<offsets[u+1];++s)slot_source[s]=u;
 for(const auto& [src,ids]:groups){std::vector<U> dist(n,inf),pred(n,inf);std::vector<bool> settled(n,false),wanted(n,false);U remaining=0;
  for(U i:ids){U target=std::get<2>(queries[i]);if(!wanted[target]){wanted[target]=true;++remaining;}}
  using Item=std::pair<U,U>;std::priority_queue<Item,std::vector<Item>,std::greater<Item>> heap;dist[src]=initial[src];heap.emplace(dist[src],src);
  while(!heap.empty()&&remaining){auto [delay,u]=heap.top();heap.pop();if(settled[u]||dist[u]!=delay)continue;settled[u]=true;if(wanted[u]){wanted[u]=false;--remaining;}
   for(U s=offsets[u];s<offsets[u+1];++s){U v=dest[s];if(!capacity[v])continue;if(weight[s]>=inf-delay)throw std::runtime_error("distance overflow");U next=delay+weight[s];if(next<dist[v]){dist[v]=next;pred[v]=s;heap.emplace(next,v);}}
  }
  for(U i:ids){auto [cid,source,target]=queries[i];std::cout<<"{\"connection_id\":"<<cid<<",\"minimum_integer\":";
   if(!settled[target]){std::cout<<"null,\"slots\":null}\n";continue;}std::cout<<dist[target]<<",\"slots\":[";std::vector<U> path;U u=target;
   while(u!=src){U s=pred[u];if(s==inf||path.size()>=n)throw std::runtime_error("bad predecessor");path.push_back(s);u=slot_source[s];}
   std::reverse(path.begin(),path.end());for(U j=0;j<path.size();++j){if(j)std::cout<<',';std::cout<<path[j];}std::cout<<"]}\n";
  }
 }
 return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 2;}}
