"""Isolated file-partial-NET seed support: preserve missing-sink lookahead delay."""
import json,sys,subprocess,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
B=R/'build/native_partial_net_lookahead_v1_2026-10-18';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items())
base=R/'build/native_candidate_move_accept_scoped_2026-10-06';D=R/'build/native_partial_net_firstpass_v1_2026-10-18';D.mkdir();src=D/'source';src.mkdir();old=B/'source/route.cpp';text=old.read_text()
text=text.replace('thread_local bool routecast_retained_pending=false;', 'thread_local bool routecast_retained_pending=false;\nthread_local std::vector<unsigned char> routecast_firstpass_partial;')
text=text.replace('    auto& device_ctx = g_vpr_ctx.mutable_device();', '    routecast_firstpass_partial.clear(); // Every invocation, including recursive and no-seed calls.\n    auto& device_ctx = g_vpr_ctx.mutable_device();',1)
needle='        VTR_LOG("ROUTECAST NET-aware seed imported feasible=%d with actual router options\\n", int(feasible));'
assert text.count(needle)==1
addition=r'''
        const char* preserve = std::getenv("ROUTECAST_PRESERVE_PARTIAL_FIRST_ITERATION");
        if (preserve && std::string(preserve)=="1") {
            if (!feasible || retained_input || router_opts.initial_timing != e_router_initial_timing::LOOKAHEAD)
                throw std::runtime_error("partial first-pass preservation requires feasible file seed and LOOKAHEAD");
            routecast_firstpass_partial.assign(route_ctx.route_trees.size(),0);
            size_t eligible=0,present_total=0,pending_total=0;
            for(auto net:net_list.nets()) {
                if(net_list.net_is_ignored(net) || !route_ctx.route_trees[net]) continue;
                const auto& tree=route_ctx.route_trees[net].value();
                if(tree.root().inode!=route_ctx.net_rr_terminals[net][0])
                    throw std::runtime_error("partial preservation SOURCE mismatch");
                size_t present=0,pending=0;
                for(size_t pin=1;pin<net_list.net_pins(net).size();++pin) {
                    auto sink=tree.find_by_isink(pin);
                    if(!sink){++pending;continue;}
                    if(sink->inode!=route_ctx.net_rr_terminals[net][pin])
                        throw std::runtime_error("partial preservation SINK mismatch");
                    ++present;
                }
                if(present && pending) {
                    routecast_firstpass_partial[size_t(net)]=1;
                    ++eligible;present_total+=present;pending_total+=pending;
                }
            }
            VTR_LOG("ROUTECAST first-pass partial eligibility nets=%zu present=%zu pending=%zu\n",eligible,present_total,pending_total);
        }
'''
text=text.replace(needle,needle+addition)
with (src/'route.cpp').open('x') as f:f.write(text)
vendor=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_net.cpp'
nettext=vendor.read_text();condition='    if (num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1 || ripup_high_fanout_nets) {';assert nettext.count(condition)==1
nettext=nettext.replace('#include "stats.h"','#include "stats.h"\n#include <vector>\nextern thread_local std::vector<unsigned char> routecast_firstpass_partial;')
nettext=nettext.replace(condition,'''    const size_t routecast_index=size_t(net_id);
    const bool routecast_preserve=itry==1 && routecast_index<routecast_firstpass_partial.size() && routecast_firstpass_partial[routecast_index];
    if ((!routecast_preserve && (num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1)) || ripup_high_fanout_nets) {''')
with (src/'route_net.cpp').open('x') as f:f.write(nettext)
shutil.copyfile(__file__,src/'build.py');protocol=R/'build/native_seed_import_v2_2026-10-06/protocol.json';p=json.loads(protocol.read_text());obj=D/'route.o';compile=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(obj)]
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(D/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(R/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1];link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(obj),str(base/'sync_once.o'),str(D/'route_net.o'),wrap]
inputs=[bp,old,protocol,base/'libvpr.a',base/'read_route.o',base/'old_traceback.o',base/'sync_once.o'];bindings={**closure([Path(__file__)]),**b['bindings'],str(vendor):sha(vendor),**{str(p):sha(p) for p in inputs}}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,compile=compile,link=link,old_binary_sha256=b['binary_sha256'],edit='Opt-in validated file partial NET first-pass reuse through unchanged native pruning; hold forced ripup preserved.',scope='New isolated build; no partial import, runtime correctness or no-seed/full-NET equivalence claimed until actual validation.'),f,indent=2)
print('PARTIAL NET BUILD COMPILE START',flush=True)
with (D/'compile.log').open('x') as log:subprocess.run(compile,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=None)
netcompile=[*p['compile'][:-4],'-c',str(src/'route_net.cpp'),'-o',str(D/'route_net.o')]
with (D/'compile_net.log').open('x') as log:subprocess.run(netcompile,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=None)
print('PARTIAL NET BUILD LINK START',flush=True)
with (D/'link.log').open('x') as log:subprocess.run(link,cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=None)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings={**bindings,str(src/'route.cpp'):sha(src/'route.cpp'),str(src/'route_net.cpp'):sha(src/'route_net.cpp'),str(src/'build.py'):sha(src/'build.py'),str(D/'protocol.json'):sha(D/'protocol.json')},binary_sha256=sha(D/'sequence_vpr'),opt_in_partial_firstpass_preservation=True,runtime_equivalence_pending=True,partial_seed_completion_pending=True),f,indent=2)
print('PARTIAL NET ISOLATED BUILD PASS',flush=True)
