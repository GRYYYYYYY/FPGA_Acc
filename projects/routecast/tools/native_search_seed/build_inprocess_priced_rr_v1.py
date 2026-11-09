"""Native live-RR hybrid floor probe; exact original bidi search body and reverse-index order."""
import json,subprocess,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();base=R/'build/native_inprocess_forward_rr_v2_2026-10-10';inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';D=R/'build/native_inprocess_priced_rr_v1_2026-10-10';assert not D.exists();D.mkdir();S=D/'source';S.mkdir();bp=base/'receipt.json';b=json.loads(bp.read_text());assert all(sha(p)==h for p,h in b['bindings'].items()) and all(sha(p)==h for p,h in b['source_sha256'].items());original=R/'tools/soft_demand_cpp/bidirectional_workspace_v2.cpp';text=original.read_text();proxy=r'''#include <unordered_map>
struct NativeDest {
 const RRGraphView& graph;const std::vector<U>& row;
 NativeDest(const RRGraphView& g,const std::vector<U>& r):graph(g),row(r){}
 U source(U edge)const {auto it=std::upper_bound(row.begin(),row.end(),edge);if(it==row.begin() || it==row.end())throw std::out_of_range("native edge");return U(it-row.begin()-1);}
 U operator[](U edge)const {U u=source(edge);return size_t(graph.edge_sink_node(RRNodeId(u),edge-row[u]));}
 size_t size()const{return row.back();}
};
struct NativeInc {
 NativeDest edges;const U* costs;
 NativeInc(const RRGraphView& g,const std::vector<U>& r,const U* c):edges(g,r),costs(c){}
 U operator[](U edge)const {U u=edges.source(edge);return costs[edges.graph.edge_switch(RRNodeId(u),edge-edges.row[u])];}
};
struct NativeCap {const RRGraphView& graph;explicit NativeCap(const RRGraphView& g):graph(g){} U operator[](U n)const{return graph.node_capacity(RRNodeId(n));}};
'''
text=text.replace('#include "tree_workspace_radix_stats_v4.cpp"',proxy);text=text.replace('std::vector<U> row,dest,inc,cap,rr,rd,re;','std::vector<U> row,rr,rd,re;NativeDest dest;NativeInc inc;NativeCap cap;')
old='Bidi(U size,const U* r,const U* d,const U* i,const U* c):n(size),row(r,r+size+1),dest(d,d+r[size]),inc(i,i+r[size]),cap(c,c+size),rr(size+1,0)'
new='Bidi(const RRGraphView& graph,U size,const U* r,const U* costs):n(size),row(r,r+size+1),rr(size+1,0),dest(graph,row),inc(graph,row,costs),cap(graph)'
assert old in text;text=text.replace(old,new);start=text.index('extern "C" void* rc_bidi_create(');end=text.index('extern "C" void rc_bidi_destroy',start);text=text[:start]+text[end:];(S/'native_bidi_kernel.h').write_text(text);(S/'native_forward_kernel.h').write_text((base/'source/native_forward_kernel.h').read_text());s=(base/'source/route.cpp').read_text().replace('#include "native_forward_kernel.h"','#include "native_forward_kernel.h"\n#include <set>\n#include "native_bidi_kernel.h"');s=s.replace('Workspace workspace(rr.num_nodes());size_t completed=0;','Workspace workspace(rr.num_nodes());Bidi bidi(rr,rr.num_nodes(),row.data(),switch_cost);std::vector<U> bidi_slots(rr.num_nodes());size_t completed=0;')
needle='            int status=rc_tree_workspace_native('
position=s.index(needle);branch=r'''            std::set<U> unique_targets(targets.begin(),targets.end());
            if(unique_targets.size()==1) {
                U count=0,delay=0,low=0,high=0,stats[4]={};U sink=*unique_targets.begin();
                int code=rc_bidi_search(&bidi,source,sink,0,0,price.data(),bidi_slots.data(),bidi_slots.size(),&count,&delay,&low,&high,stats);
                if(code)throw std::runtime_error("native bidirectional floor rejected");
                for(const auto& q:entry.second) {
                    std::fprintf(fp,"Q\t%llu\t%llu\t%llu",(unsigned long long)q.cid,(unsigned long long)delay,(unsigned long long)count);
                    for(U i=0;i<count;++i)std::fprintf(fp,"\t%llu",(unsigned long long)bidi_slots[i]);std::fprintf(fp,"\n");++completed;
                }
                continue;
            }
'''
s=s[:position]+branch+s[position:];s=s.replace('source,sink,0,0,price.data()','source,sink,0,search_weight,price.data()').replace('source,0,0,targets.data()','source,0,search_weight,targets.data()');needle='        std::vector<uint8_t> settled(rr.num_nodes());';assert s.count(needle)==1;s=s.replace(needle,'        U search_weight=0;\n        if(const char* price_file=std::getenv("ROUTECAST_INPROCESS_PRICES")) {\n            std::ifstream prices_input(price_file);if(!prices_input)throw std::runtime_error("price open failed");\n            std::set<U> priced;U node,value;\n            while(prices_input>>node) {\n                if(!(prices_input>>value) || node>=rr.num_nodes() || !priced.insert(node).second)throw std::runtime_error("invalid price input");\n                price[node]=value;\n            }\n            if(!prices_input.eof())throw std::runtime_error("price parse failed");\n            search_weight=50000000ULL;\n        }\n'+needle);(S/'route.cpp').write_text(s);(S/'build.py').write_text(Path(__file__).read_text());p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());bindings={**b['bindings'],str(bp):sha(bp),str(original):sha(original),str(Path(__file__)):sha(Path(__file__))};cmd=[*p['compile'][:-4],'-c',str(S/'route.cpp'),'-o',str(D/'route.o')]
with (D/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(D/'route.o'),str(inputs/'sync_once.o'),wrap]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),source_sha256={str(p):sha(p) for p in S.iterdir()},scope='Controlled frozen-price native RR hybrid searches; weight 50000000. No transaction edits. Original bidi search body preserved; reverse node/edge indices constructed in original order. Not full feedback/predictor/zero-memory/fulltime gain.'),indent=2)+'\n');print('NATIVE INPROCESS HYBRID BUILT')
