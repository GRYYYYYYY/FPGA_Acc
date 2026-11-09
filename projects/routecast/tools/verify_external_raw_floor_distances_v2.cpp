#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>
#include <vector>
using U=uint64_t;
U word(std::ifstream& f){U v;if(!f.read(reinterpret_cast<char*>(&v),8))throw std::runtime_error("truncated");return v;}
std::vector<U> words(std::ifstream& f,U n){std::vector<U>a(n);for(auto& v:a)v=word(f);return a;}
int main(int argc,char**argv){try{
 if(argc!=3)throw std::runtime_error("input expected-values");std::ifstream f(argv[1],std::ios::binary);if(word(f)!=0x5243464c4f4f5231ULL)throw std::runtime_error("magic");U n=word(f),m=word(f),q=word(f);auto off=words(f,n+1),dest=words(f,m),weight=words(f,m),cap=words(f,n),initial=words(f,n);std::vector<std::vector<std::pair<U,U>>> forward(n);
 for(U sink=0;sink<n;++sink)for(U s=off[sink];s<off[sink+1];++s)forward.at(dest[s]).emplace_back(sink,weight[s]);
 std::map<U,std::vector<std::pair<U,U>>> groups;std::set<U> cids;
 for(U i=0;i<q;++i){U cid=word(f),sink=word(f),source=word(f);if(!cids.insert(cid).second||source>=n||sink>=n||!cap[source]||!cap[sink])throw std::runtime_error("query");groups[source].emplace_back(cid,sink);}
 std::map<U,U> expected;std::ifstream ef(argv[2]);U cid,value;while(ef>>cid>>value)if(!expected.emplace(cid,value).second)throw std::runtime_error("duplicate expected");if(expected.size()!=q)throw std::runtime_error("expected coverage");
 const U inf=std::numeric_limits<U>::max();U checked=0;
 for(const auto& [source,queries]:groups){std::vector<U> dist(n,inf);std::set<U> wanted;for(auto [id,target]:queries)wanted.insert(target);std::set<std::pair<U,U>> queue;dist[source]=0;queue.emplace(0,source);
  while(!queue.empty()&&!wanted.empty()){auto item=*queue.begin();queue.erase(queue.begin());auto [du,u]=item;wanted.erase(u);
   for(auto [v,w]:forward[u])if(cap[v]){if(w>=inf-du)throw std::runtime_error("overflow");U dv=du+w;if(dv<dist[v]){queue.erase({dist[v],v});dist[v]=dv;queue.emplace(dv,v);}}
  }
  for(auto [id,target]:queries){if(!expected.count(id)||dist[target]!=expected.at(id))throw std::runtime_error("distance disagreement");++checked;}
 }
 if(checked!=q)throw std::runtime_error("coverage");std::cout<<"FORWARD_SET_DIJKSTRA_ALL_FLOORS_PASS "<<checked<<' '<<groups.size()<<'\n';
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 2;}return 0;}
