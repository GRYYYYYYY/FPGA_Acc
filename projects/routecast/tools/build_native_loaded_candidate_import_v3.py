"""Private candidate import branch preserving existing native state frames."""
import json
import re
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/native_candidate_move_accept_scoped_2026-10-06'
source=ROOT/'build/native_candidate_multi_pair_2026-10-06/source/route.cpp'
out=ROOT/'build/native_loaded_candidate_import_v3_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
p=json.loads((ROOT/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text())
shared={f:sha(f) for f in p['inputs_sha256']}
s=source.read_text()
s=s.replace('        bool placement_committed=false;', '        auto saved_placement_id=g_vpr_ctx.placement().placement_id;\n        bool placement_committed=false;',1)
needle='            bool candidate_ok=route(net_list,width_fac,router_opts,analysis_opts,det_routing_arch,segment_inf,net_delay,timing_info,delay_calc,chan_width_dist,directs,first_iteration_priority,is_flat);'
assert s.count(needle)==1
s=s.replace(needle,'''            bool candidate_ok=false;
            const char* candidate_path=std::getenv("ROUTECAST_IMPORTED_CANDIDATE");
            if(candidate_path && *candidate_path) {
                if(sequence.size()!=1)throw std::runtime_error("import probe requires single step");
                g_vpr_ctx.mutable_placement().placement_id=print_place("design.net",mutable_cluster.clb_nlist.netlist_id().c_str(),"candidate.place",registry.block_locs());
                candidate_ok=read_route(candidate_path,router_opts,true,is_flat);
                for(auto net:net_list.nets()) {
                    if(!route_ctx.route_trees[net])continue;
                    for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                        auto sink=route_ctx.route_trees[net]->find_by_isink(pin);
                        if(!sink)throw std::runtime_error("imported candidate incomplete sink delay");
                        net_delay[net][pin]=sink->Tdel;
                    }
                }
                VTR_LOG("ROUTECAST imported external candidate in loaded context with refreshed sink delay matrix\\n");
            } else {
'''+needle.replace('bool candidate_ok=','candidate_ok=')+'''
            }
'''.replace('bool candidate_ok=route','candidate_ok=route'))
s=s.replace('            VTR_LOG("ROUTECAST restored routing and inverse committed placement before STA rebuild', '            g_vpr_ctx.mutable_placement().placement_id=saved_placement_id;\n            VTR_LOG("ROUTECAST restored routing and inverse committed placement before STA rebuild',1)
s=s.replace('        for(size_t step=0;step<sequence.size();++step) {', '''        if(std::getenv("ROUTECAST_IMPORTED_CANDIDATE")) {
            bool initial_quiet=false;
            sync_netlists_to_routing(net_list,device_ctx,g_vpr_ctx.mutable_atom(),g_vpr_ctx.mutable_clustering(),g_vpr_ctx.placement(),initial_quiet);
            VTR_LOG("ROUTECAST seed packing synchronized before accepted state frame\\n");
        }
        for(size_t step=0;step<sequence.size();++step) {''',1)
(src/'route.cpp').write_text(s)
compile_cmd=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(out/'route.o')]
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'import_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']]
link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(ROOT/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(out/'route.o'),str(base/'sync_once.o'),wrap]
(out/'protocol.json').write_text(json.dumps(dict(compile=compile_cmd,link=link,shared_inputs_sha256=shared,parent_source_sha256=sha(source),source_sha256=sha(src/'route.cpp')),indent=2)+'\n')
for label,cmd in [('compile',compile_cmd),('link',link)]:
    with (out/(label+'.log')).open('w') as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
    if code:raise SystemExit(label+' failed '+str(code))
assert all(sha(f)==h for f,h in shared.items())
(out/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(out/'import_vpr'),protocol_sha256=sha(out/'protocol.json'),scope='Single-step external route import after compatible swap, delay refresh, existing packing/STA/frame rollback. Execution and quality selection unverified.'),indent=2)+'\n')
print('built loaded candidate import')
