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
struct Label{Cost cost=0;U hops=0,parent=UINT64_MAX,edge=UINT64_MAX;};
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
 std::vector<Label> best(n);std::vector<bool> known(n),settled(n);std::vector<U> heap,pos(n,UINT64_MAX);U visits=0,count=0;
 auto path=[&](U node){std::vector<U> result;while(best[node].parent!=UINT64_MAX){result.push_back(best[node].edge);node=best[node].parent;if(result.size()>n)throw std::runtime_error("parent cycle");}std::reverse(result.begin(),result.end());return result;};
 auto less=[&](U a,U b){if(best[a].cost!=best[b].cost)return best[a].cost<best[b].cost;if(best[a].hops!=best[b].hops)return best[a].hops<best[b].hops;auto pa=path(a),pb=path(b);if(pa!=pb)return pa<pb;return ids[a]<ids[b];};
 auto swap=[&](U a,U b){std::swap(heap[a],heap[b]);pos[heap[a]]=a;pos[heap[b]]=b;};
 auto up=[&](U i){while(i){U p=(i-1)/2;if(!less(heap[i],heap[p]))break;swap(i,p);i=p;}};
 auto insert=[&](U r){if(pos[r]==UINT64_MAX){pos[r]=heap.size();heap.push_back(r);}up(pos[r]);};
 if(caps[source]){known[source]=true;insert(source);}
 std::vector<U> found;
 while(!heap.empty()){
 U r=heap[0],last=heap.back();heap.pop_back();pos[r]=UINT64_MAX;
 if(!heap.empty()){heap[0]=last;pos[last]=0;U i=0;while(2*i+1<heap.size()){U c=2*i+1;if(c+1<heap.size()&&less(heap[c+1],heap[c]))++c;if(!less(heap[c],heap[i]))break;swap(i,c);i=c;}}
 settled[r]=true;++count;
 if(target[r]){found.push_back(r);if(--remain==0)break;}
 for(U i=rows[r];i<rows[r+1];++i){++visits;U d=dst[i];if(settled[d]||weights[i]==UINT64_MAX)continue;
 Label next{best[r].cost+weights[i],best[r].hops+1,r,edges[i]};bool better=!known[d]||next.cost<best[d].cost||(next.cost==best[d].cost&&next.hops<best[d].hops);
 if(known[d]&&next.cost==best[d].cost&&next.hops==best[d].hops){auto candidate=path(r);candidate.push_back(edges[i]);better=candidate<path(d);}
 if(better){known[d]=true;best[d]=next;insert(d);}
 }
 }
 std::cout<<"{\"settled_nodes\":"<<count<<",\"edge_visits\":"<<visits<<",\"budget_exhausted\":false,\"paths\":{";
 for(size_t i=0;i<found.size();++i){U r=found[i];if(i)std::cout<<',';std::cout<<'"'<<ids[r]<<"\":[";auto output=path(r);for(size_t j=0;j<output.size();++j){if(j)std::cout<<',';std::cout<<output[j];}std::cout<<']';}std::cout<<"}}\n"<<std::flush;
 };
 if(batch){std::string line;while(std::getline(std::cin,line)){std::istringstream in(line);std::vector<std::string> args;std::string token;while(in>>token)args.push_back(token);query(args);}}
 else{std::vector<std::string> args;for(int i=2;i<argc;++i)args.emplace_back(argv[i]);query(args);}
 return 0;
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
