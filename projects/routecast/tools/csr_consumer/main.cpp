// Host reference consumer only. Caller must authenticate v1 manifest/payloads.
#include <algorithm>
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
struct Label{Cost cost;U hops;std::vector<U> path;};
bool less(const Label&a,const Label&b){if(a.cost!=b.cost)return a.cost<b.cost;if(a.hops!=b.hops)return a.hops<b.hops;return a.path<b.path;}
struct Entry{Label label;U rank;};
struct Greater{bool operator()(const Entry&a,const Entry&b)const{if(less(b.label,a.label))return true;if(less(a.label,b.label))return false;return a.rank>b.rank;}};
int main(int argc,char**argv){try{
 if(argc<3 || (argc<4 && std::string(argv[2])!="--batch"))throw std::runtime_error("usage: csr_consumer authenticated_csr source sink...");
 std::string dir=argv[1];auto ids=load<U>(dir,"node_ids"),rows=load<U>(dir,"row_offsets"),edges=load<U>(dir,"edge_ids"),dst=load<U>(dir,"dest_ranks"),weights=load<U>(dir,"costs"),caps=load<U>(dir,"capacities");auto types=load<uint8_t>(dir,"types");
 U n=ids.size(),m=edges.size();if(!n||rows.size()!=n+1||rows[0]!=0||rows.back()!=m||dst.size()!=m||weights.size()!=m||caps.size()!=n||types.size()!=n||!std::is_sorted(ids.begin(),ids.end())||std::adjacent_find(ids.begin(),ids.end())!=ids.end()||!std::is_sorted(rows.begin(),rows.end()))throw std::runtime_error("invalid CSR");
 std::vector<bool> seen(m);for(U i=0;i<m;++i){if(dst[i]>=n||edges[i]>=m||seen[edges[i]])throw std::runtime_error("invalid edge mapping");seen[edges[i]]=true;}
 auto rank=[&](const char*s){size_t used=0;std::string text(s);if(text.empty()||text[0]=='-')throw std::runtime_error("invalid ID");U raw=std::stoull(text,&used);if(used!=text.size())throw std::runtime_error("invalid ID");auto it=std::lower_bound(ids.begin(),ids.end(),raw);if(it==ids.end()||*it!=raw)throw std::runtime_error("unknown ID");return U(it-ids.begin());};
 bool batch=std::string(argv[2])=="--batch";
 auto query=[&](const std::vector<std::string>& args){
 if(args.size()<2)throw std::runtime_error("empty/missing batch endpoints");
 U source=rank(args[0].c_str());if(types[source]!=0)throw std::runtime_error("invalid SOURCE");std::vector<bool> target(n);U remain=0;for(size_t i=1;i<args.size();++i){U r=rank(args[i].c_str());if(types[r]!=1)throw std::runtime_error("invalid SINK");if(!target[r]){target[r]=true;++remain;}}
 std::vector<Label> best(n);std::vector<bool> known(n),settled(n);std::priority_queue<Entry,std::vector<Entry>,Greater> q;U visits=0,count=0;
 if(caps[source]){best[source]={0,0,{}};known[source]=true;q.push({best[source],source});}
 std::vector<U> found;
 while(!q.empty()){
 auto entry=q.top();q.pop();U r=entry.rank;if(settled[r]||less(best[r],entry.label)||less(entry.label,best[r]))continue;settled[r]=true;++count;
 if(target[r]){found.push_back(r);if(--remain==0)break;}
 for(U i=rows[r];i<rows[r+1];++i){++visits;U d=dst[i];if(settled[d]||weights[i]==std::numeric_limits<U>::max())continue;Label next=entry.label;next.cost+=weights[i];++next.hops;next.path.push_back(edges[i]);if(!known[d]||less(next,best[d])){known[d]=true;best[d]=next;q.push({std::move(next),d});}}
 }
 std::cout<<"{\"settled_nodes\":"<<count<<",\"edge_visits\":"<<visits<<",\"budget_exhausted\":false,\"paths\":{";
 for(size_t i=0;i<found.size();++i){U r=found[i];if(i)std::cout<<',';std::cout<<'"'<<ids[r]<<"\":[";for(size_t j=0;j<best[r].path.size();++j){if(j)std::cout<<',';std::cout<<best[r].path[j];}std::cout<<']';}std::cout<<"}}\n"<<std::flush;
 };
 if(batch){std::string line;while(std::getline(std::cin,line)){std::istringstream in(line);std::vector<std::string> args;std::string token;while(in>>token)args.push_back(token);query(args);}}
 else{std::vector<std::string> args;for(int i=2;i<argc;++i)args.emplace_back(argv[i]);query(args);}
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
