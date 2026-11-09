"""Same-target reference/candidate selection with canonical view restoration."""
import json
import re
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/native_candidate_move_accept_scoped_2026-10-06'
source=ROOT/'build/native_loaded_candidate_import_v3_2026-10-06/source/route.cpp'
out=ROOT/'build/loaded_native_quality_gate_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
p=json.loads((ROOT/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text())
shared={f:sha(f) for f in p['inputs_sha256']}
s=source.read_text()
needle='        bool placement_committed=false;'
s=s.replace(needle,'''        float reference_cpd=-1;
        auto canonical_reset=[&]() {
            for(const auto& entry:canonical_pb)*entry.first=entry.second;
            mutable_atom.lookup=canonical_lookup;
            mutable_cluster.post_routing_clb_pin_nets=canonical_post;
            mutable_cluster.pre_routing_net_pin_mapping=canonical_pre;
        };
        auto import_delays=[&](const char* path) {
            if(!read_route(path,router_opts,true,is_flat))throw std::runtime_error("quality gate import infeasible");
            for(auto net:net_list.nets()) {
                if(!route_ctx.route_trees[net])continue;
                for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                    auto sink=route_ctx.route_trees[net]->find_by_isink(pin);
                    if(!sink)throw std::runtime_error("quality gate missing sink");
                    net_delay[net][pin]=sink->Tdel;
                }
            }
        };
'''+needle,1)
needle='                candidate_ok=read_route(candidate_path,router_opts,true,is_flat);'
s=s.replace(needle,'''                if(std::getenv("ROUTECAST_SAME_TARGET_GATE")) {
                    if(sequence!="A")throw std::runtime_error("quality gate requires single commit step");
                    bool reference_ok=route(net_list,width_fac,router_opts,analysis_opts,det_routing_arch,segment_inf,net_delay,timing_info,delay_calc,chan_width_dist,directs,first_iteration_priority,is_flat);
                    if(!reference_ok)throw std::runtime_error("quality gate reference route failed");
                    check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
                    FILE* reference_file=std::fopen("loaded_reference.route","w");
                    if(!reference_file)throw std::runtime_error("reference capture failed");
                    print_route(net_list,reference_file,is_flat);
                    if(std::fclose(reference_file))throw std::runtime_error("reference capture close failed");
                    bool quiet_reference=false;
                    sync_netlists_to_routing(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement(),quiet_reference);
                    refresh();reference_cpd=std::get<0>(metrics());
                    canonical_reset();
                }
'''+needle,1)
needle="            if(sequence[step]=='A') {"
s=s.replace(needle,'''            if(reference_cpd>=0) {
                float predicted_cpd=std::get<0>(metrics());
                bool pick_reference=predicted_cpd>reference_cpd;
                if(pick_reference) {
                    canonical_reset();import_delays("loaded_reference.route");
                    check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
                    bool quiet_reference=false;
                    sync_netlists_to_routing(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement(),quiet_reference);
                    refresh();
                    if(std::get<0>(metrics())!=reference_cpd)throw std::runtime_error("selected reference STA mismatch");
                }
                VTR_LOG("ROUTECAST same-target gate predicted_cpd_ns=%.9g reference_cpd_ns=%.9g selected=%s\\n",1.e9*predicted_cpd,1.e9*reference_cpd,pick_reference?"reference":"predicted");
            }
'''+needle,1)
(src/'route.cpp').write_text(s)
compile_cmd=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(out/'route.o')]
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'gate_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']]
link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(ROOT/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(out/'route.o'),str(base/'sync_once.o'),wrap]
(out/'protocol.json').write_text(json.dumps(dict(compile=compile_cmd,link=link,shared_inputs_sha256=shared,parent_source_sha256=sha(source),source_sha256=sha(src/'route.cpp')),indent=2)+'\n')
for label,cmd in [('compile',compile_cmd),('link',link)]:
    with (out/(label+'.log')).open('w') as stream:code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
    if code:raise SystemExit(label+' failed '+str(code))
assert all(sha(f)==h for f,h in shared.items())
(out/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(out/'gate_vpr'),protocol_sha256=sha(out/'protocol.json'),scope='One-step same-target CPD gate; reference winner reimport resets search cost metadata, not exact full router checkpoint restoration. Runtime/quality/evidence pending.'),indent=2)+'\n')
print('built loaded same-target quality gate')
