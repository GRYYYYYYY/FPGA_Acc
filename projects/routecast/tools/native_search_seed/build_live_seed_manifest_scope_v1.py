"""Explicit manifest graph/query dimensions; unchanged exact adaptive kernels."""
import json,subprocess,re,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();base=R/'build/native_live_seed_adaptive_width_v1_2026-10-10';D=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';assert not D.exists();D.mkdir();S=D/'source';S.mkdir();b=json.loads((base/'receipt.json').read_text());assert all(sha(p)==h for p,h in b['bindings'].items()) and all(sha(p)==h for p,h in b['source_sha256'].items())
for name in ['native_forward_kernel.h','native_bidi_kernel.h','native_forward_kernel64.h','native_bidi_kernel64.h']:shutil.copyfile(base/'source'/name,S/name)
s=(base/'source/route.cpp').read_text();edits=[]
def replace(a,c):
 global s
 assert s.count(a)==1,a;edits.append((a,c));s=s.replace(a,c)
replace('if(rr.num_nodes()!=91088 || rr.num_rr_switches()!=4)throw std::runtime_error("unsupported inprocess exact graph");','''std::ifstream dimensions(manifest);char marker;U expected_nodes,expected_edges,expected_queries;
        if(!(dimensions>>marker>>expected_nodes>>expected_edges>>expected_queries) || marker!='G' || !expected_nodes || !expected_edges || !expected_queries || rr.num_nodes()!=expected_nodes || rr.num_rr_switches()!=4)throw std::runtime_error("unsupported manifest graph dimensions");''')
replace('if(row.back()!=801735)throw std::runtime_error("unsupported inprocess edges");','if(row.back()!=expected_edges)throw std::runtime_error("manifest edge count mismatch");')
replace('VTR_LOG("ROUTECAST global edge preflight nodes=91088 edges=801735 exact rows/capacity/source/sink/switch\\n");','VTR_LOG("ROUTECAST global edge preflight nodes=%zu edges=%llu exact rows/capacity/source/sink/switch\\n",rr.num_nodes(),(unsigned long long)row.back());')
replace('std::map<U,std::pair<U,U>> netmeta;std::map<U,std::vector<Query>> queries;char kind;','std::map<U,std::pair<U,U>> netmeta;std::map<U,std::vector<Query>> queries;std::set<U> cids;bool header=false;char kind;')
replace("if(kind=='N') {if(!(input>>a>>b>>c)","if(kind=='G') {if(header || !netmeta.empty() || !queries.empty() || !(input>>a>>b>>c) || a!=expected_nodes || b!=expected_edges || c!=expected_queries)throw std::runtime_error(\"invalid graph header\");header=true;}\n            else if(kind=='N') {if(!header || !(input>>a>>b>>c)")
replace("else if(kind=='Q') {if(!(input>>a>>b>>c>>d>>e))", "else if(kind=='Q') {if(!header || !(input>>a>>b>>c>>d>>e) || !c || d>=expected_nodes || e>=expected_nodes || !cids.insert(a).second)")
replace('size_t netcount=0;','''if(!input.eof() || !header || cids.size()!=expected_queries)throw std::runtime_error("incomplete manifest scope");
        for(const auto& entry:netmeta){
            const auto count=entry.second.second;const bool required=!entry.second.first && count>1;
            if(required!=bool(queries.count(entry.first)))throw std::runtime_error("query NET coverage mismatch");
            if(required){std::set<U> pins;for(const auto& q:queries.at(entry.first))if(q.pin>=count || !pins.insert(q.pin).second)throw std::runtime_error("duplicate or invalid query pin");if(pins.size()!=count-1)throw std::runtime_error("query pin coverage mismatch");}
        }
        for(const auto& entry:queries)if(!netmeta.count(entry.first))throw std::runtime_error("unknown query NET");
        size_t netcount=0;''')
replace('Wide bound=Wide(2)*rr.num_nodes()*step;','Wide bound=Wide(2)*rr.num_nodes()*step;\n            if(bound>=(Wide(1)<<120))throw std::runtime_error("exact cost envelope exceeded");')
replace('std::fprintf(fp,"READY\\t%zu\\t6273\\n",queries.size());','std::fprintf(fp,"READY\\t%zu\\t%llu\\n",queries.size(),(unsigned long long)expected_queries);')
replace('completed!=6273','completed!=expected_queries')
restored=s
for a,c in reversed(edits):restored=restored.replace(c,a)
assert restored==(base/'source/route.cpp').read_text();(S/'route.cpp').write_text(s);(S/'build.py').write_text(Path(__file__).read_text())
p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';bindings={**b['bindings'],str(base/'receipt.json'):sha(base/'receipt.json'),str(Path(__file__)):sha(Path(__file__))}
cmd=[*p['compile'][:-4],'-c',str(S/'route.cpp'),'-o',str(D/'route.o')]
with (D/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(D/'route.o'),str(inputs/'sync_once.o'),wrap]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),source_sha256={str(p):sha(p) for p in S.iterdir()},edits=edits,source_reversible=True,scope='Manifest dimension and complete pin/query/NET validation; unchanged four kernels and native router; same zero nodeRC/four exact switches only. No generic nonzeroRC or execution evidence.'),indent=2)+'\n');print('MANIFEST SCOPE NATIVE BUILD PASS')
