// Host workspace-reuse experiment; identical direct_search validation/reset.
// Host reference consumer only. Caller must authenticate v1 manifest/payloads.
#include <algorithm>
#include "indexed_heap.hpp"
#include "predecessor_path.hpp"
#include "workspace_search.hpp"
#include "direct_search.hpp"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <queue>
#include <stdexcept>
#include <string>
#include <sstream>
#include <tuple>
#include <vector>
using U=uint64_t;
// Settled predecessor paths are simple: at most n-1 edges.
// n and every edge cost fit uint64, so their sum fits unsigned 128.
using Cost=unsigned __int128;
template<class T> std::vector<T> load(const std::string& dir,const std::string& name){
 std::ifstream f(dir+"/"+name+".bin",std::ios::binary|std::ios::ate);
 if(!f)throw std::runtime_error("missing payload");
 auto bytes=f.tellg();if(bytes<0 || bytes%sizeof(T))throw std::runtime_error("payload size");
 std::vector<T> v(static_cast<size_t>(bytes)/sizeof(T));f.seekg(0);
 // Explicit little-endian decoding, independent of host byte order.
 for(auto& x:v){U y=0;for(size_t j=0;j<sizeof(T);++j){char c;if(!f.get(c))throw std::runtime_error("short payload");y|=U(static_cast<unsigned char>(c))<<(8*j);}x=static_cast<T>(y);}return v;
}
struct Label{Cost cost=0;U hops=0,parent=UINT64_MAX,edge=UINT64_MAX;};
int main(int argc,char**argv){try{
 if(argc<3 || (argc<4 && std::string(argv[2])!="--batch"))throw std::runtime_error("usage: csr_consumer authenticated_csr source sink...");
 std::string dir=argv[1];auto ids=load<U>(dir,"node_ids"),rows=load<U>(dir,"row_offsets"),edges=load<U>(dir,"edge_ids"),dst=load<U>(dir,"dest_ranks"),weights=load<U>(dir,"costs"),caps=load<U>(dir,"capacities");auto types=load<uint8_t>(dir,"types");
 U n=ids.size(),m=edges.size();if(!n||rows.size()!=n+1||rows[0]!=0||rows.back()!=m||dst.size()!=m||weights.size()!=m||caps.size()!=n||types.size()!=n||!std::is_sorted(ids.begin(),ids.end())||std::adjacent_find(ids.begin(),ids.end())!=ids.end()||!std::is_sorted(rows.begin(),rows.end()))throw std::runtime_error("invalid CSR");
 std::vector<bool> seen(m);for(U i=0;i<m;++i){if(dst[i]>=n||edges[i]>=m||seen[edges[i]])throw std::runtime_error("invalid edge mapping");seen[edges[i]]=true;}
 auto rank=[&](const char*s){size_t used=0;std::string text(s);if(text.empty()||text[0]=='-')throw std::runtime_error("invalid ID");U raw=std::stoull(text,&used);if(used!=text.size())throw std::runtime_error("invalid ID");auto it=std::lower_bound(ids.begin(),ids.end(),raw);if(it==ids.end()||*it!=raw)throw std::runtime_error("unknown ID");return U(it-ids.begin());};
 bool batch=std::string(argv[2])=="--batch";
 std::vector<routecast::SearchLabel> best(n);std::vector<uint8_t> known(n),settled(n);std::vector<U> storage(n),pos(n),scratch(n),left(n),right(n);
 auto query=[&](const std::vector<std::string>& args){
 if(args.size()<2)throw std::runtime_error("empty/missing batch endpoints");
 U source=rank(args[0].c_str());if(types[source]!=0)throw std::runtime_error("invalid SOURCE");std::vector<U> targets;for(size_t i=1;i<args.size();++i){U r=rank(args[i].c_str());if(types[r]!=1)throw std::runtime_error("invalid SINK");targets.push_back(r);}
 std::sort(targets.begin(),targets.end());targets.erase(std::unique(targets.begin(),targets.end()),targets.end());
 routecast::SearchWorkspace workspace{best.data(),known.data(),settled.data(),pos.data(),storage.data(),scratch.data(),left.data(),right.data(),n,n,n};
 routecast::PreparedSearchGraph graph{rows.data(),edges.data(),dst.data(),weights.data(),caps.data(),types.data(),n,m};routecast::SearchCounters counters;
 auto termination=routecast::direct_search(rows.data(),edges.data(),dst.data(),weights.data(),caps.data(),types.data(),n,m,source,targets.data(),targets.size(),n,best.data(),known.data(),settled.data(),pos.data(),storage.data(),left.data(),right.data(),n,n,n,counters);
 if(termination!=routecast::SearchTermination::targets_complete&&termination!=routecast::SearchTermination::frontier_empty)throw std::runtime_error("nonterminal search failure");
 U count=counters.settled,visits=counters.edge_visits;std::vector<U> found;for(U t:targets)if(settled[t])found.push_back(t);
 auto path=[&](U node,U* output){U length=0;auto parent=[&](U r){return best[r].parent;};auto edge=[&](U r){return best[r].edge;};if(routecast::reconstruct_path(node,source,n,parent,edge,scratch.data(),n,output,n,length)!=routecast::PathStatus::ok)throw std::runtime_error("path reconstruction failure");return length;};
 std::cout<<"{\"settled_nodes\":"<<count<<",\"edge_visits\":"<<visits<<",\"budget_exhausted\":false,\"paths\":{";
 for(size_t i=0;i<found.size();++i){U r=found[i];if(i)std::cout<<',';std::cout<<'"'<<ids[r]<<"\":[";U length=path(r,left.data());for(U j=0;j<length;++j){if(j)std::cout<<',';std::cout<<left[j];}std::cout<<']';}std::cout<<"}}\n"<<std::flush;
 };
 if(batch){std::string line;while(std::getline(std::cin,line)){std::istringstream in(line);std::vector<std::string> args;std::string token;while(in>>token)args.push_back(token);query(args);}}
 else{std::vector<std::string> args;for(int i=2;i<argc;++i)args.emplace_back(argv[i]);query(args);}
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
