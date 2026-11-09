"""Private repeat-read probe; shared VTR source/archive remain read-only."""
import json
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'build/native_search_seed_v3_2026-10-06'
out=ROOT/'build/native_repeat_import_probe_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
p=json.loads((ROOT/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text())
prior=json.loads((base/'receipt.json').read_text())
assert all(sha(path)==h for path,h in prior['sources_sha256'].items())
shared={path:sha(path) for path in p['inputs_sha256']}
text=(base/'source/route.cpp').read_text()
text='#include "check_route.h"\n'+text
needle='        VTR_LOG("ROUTECAST NET-aware seed imported feasible=%d with actual router options\\n", int(feasible));'
assert text.count(needle)==1
text=text.replace(needle,needle+'''
        if(std::getenv("ROUTECAST_REPEAT_IMPORT")) {
            auto observations=[&]() {
                std::vector<std::tuple<ParentNetId,size_t,RRNodeId,float>> sinks;
                for(auto net:net_list.nets()) {
                    if(!route_ctx.route_trees[net])continue;
                    for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                        auto sink=route_ctx.route_trees[net]->find_by_isink(pin);
                        if(!sink)throw std::runtime_error("missing repeated import sink");
                        sinks.emplace_back(net,pin,sink->inode,sink->Tdel);
                    }
                }
                std::vector<int> occupancy;
                for(auto node:device_ctx.rr_graph.nodes())occupancy.push_back(route_ctx.rr_node_route_inf[node].occ());
                return std::make_pair(sinks,occupancy);
            };
            check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
            auto before=observations();
            bool again=read_route(routecast_seed,router_opts,true,is_flat);
            check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
            if(!again || !feasible || observations()!=before)throw std::runtime_error("repeat import state mismatch");
            VTR_LOG("ROUTECAST repeated import FULL sink-delay and occupancy parity passed sinks=%zu nodes=%zu\\n",before.first.size(),before.second.size());
        }
''')
(src/'route.cpp').write_text(text)
compile_cmd=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(out/'route.o')]
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'repeat_import_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']]
link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(out/'route.o')]
(out/'protocol.json').write_text(json.dumps(dict(compile=compile_cmd,link=link,shared_inputs_sha256=shared,source_sha256=sha(src/'route.cpp'),base_receipt_sha256=sha(base/'receipt.json')),indent=2)+'\n')
for label,cmd in [('compile',compile_cmd),('link',link)]:
    with (out/(label+'.log')).open('w') as stream:
        code=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
    if code:raise SystemExit(label+' failed: '+str(code))
assert all(sha(path)==h for path,h in shared.items())
(out/'receipt.json').write_text(json.dumps(dict(binary_sha256=sha(out/'repeat_import_vpr'),protocol_sha256=sha(out/'protocol.json'),scope='Same-placement same-NET repeated read_route FULL/sink-delay/occupancy probe, not changed candidate/STA/rollback validation.'),indent=2)+'\n')
print('built repeat import probe')
