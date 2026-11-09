"""Explicit manifest graph/query dimensions; unchanged exact adaptive kernels."""
import json,subprocess,re,sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path.cwd();base=R/'build/native_live_seed_manifest_scope_v1_2026-10-10';D=R/'build/native_indexed_cost_dump_v1_2026-10-10';assert not D.exists();D.mkdir();S=D/'source';S.mkdir();b=json.loads((base/'receipt.json').read_text());assert all(sha(p)==h for p,h in b['bindings'].items()) and all(sha(p)==h for p,h in b['source_sha256'].items())
for name in ['native_forward_kernel.h','native_bidi_kernel.h','native_forward_kernel64.h','native_bidi_kernel64.h']:shutil.copyfile(base/'source'/name,S/name)
s=(base/'source/route.cpp').read_text()
insert=r'''    if(const char* path=std::getenv("ROUTECAST_INDEXED_COST_DUMP")) {
        FILE* fp=std::fopen(path,"w");if(!fp)throw std::runtime_error("cost dump open");
        const auto& rr=device_ctx.rr_graph;
        std::fprintf(fp,"G\t%zu\t%zu\n",rr.num_nodes(),device_ctx.rr_indexed_data.size());
        for(auto id:device_ctx.rr_indexed_data.keys()) {
            const auto& d=device_ctx.rr_indexed_data[id];
            std::fprintf(fp,"I\t%zu\t%d\t%.9g\t%.9g\t%.9g\t%.9g\t%.9g\t%.9g\n",size_t(id),d.seg_index,double(d.base_cost),double(d.saved_base_cost),double(d.inv_length),double(d.T_linear),double(d.T_quadratic),double(d.C_load));
        }
        std::map<std::pair<int,size_t>,size_t> counts;
        for(auto node:rr.nodes())++counts[{int(rr.node_type(node)),size_t(rr.node_cost_index(node))}];
        for(const auto& entry:counts)std::fprintf(fp,"N\t%d\t%zu\t%zu\n",entry.first.first,entry.first.second,entry.second);
        if(std::ferror(fp) || std::fclose(fp))throw std::runtime_error("cost dump close");
        VTR_LOG("ROUTECAST indexed cost metadata exported before routing\n");std::fflush(nullptr);std::exit(0);
    }
'''
needle='    if(const char* manifest=std::getenv("ROUTECAST_INPROCESS_QUERIES")) {'
assert s.count(needle)==1;s=s.replace(needle,insert+needle)
assert s.replace(insert,'')==(base/'source/route.cpp').read_text()
edits=[('',insert)];(S/'route.cpp').write_text(s);(S/'build.py').write_text(Path(__file__).read_text())
p=json.loads((R/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());inputs=R/'build/native_candidate_move_accept_scoped_2026-10-06';bindings={**b['bindings'],str(base/'receipt.json'):sha(base/'receipt.json'),str(Path(__file__)):sha(Path(__file__))}
cmd=[*p['compile'][:-4],'-c',str(S/'route.cpp'),'-o',str(D/'route.o')]
with (D/'compile.log').open('w') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(inputs/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(inputs/'read_route.o'),str(inputs/'old_traceback.o'),str(D/'route.o'),str(inputs/'sync_once.o'),wrap]
with (D/'link.log').open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(p)==h for p,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,binary_sha256=sha(D/'sequence_vpr'),source_sha256={str(p):sha(p) for p in S.iterdir()},edits=edits,source_reversible=True,scope='Optional indexed metadata dump immediately after route structs initialization, clean exit before routing. Original path exactly restored when diagnostic insert removed; four search kernels unchanged. No native routing or runtime evidence.'),indent=2)+'\n');print('INDEXED COST DIAGNOSTIC BUILD PASS')
