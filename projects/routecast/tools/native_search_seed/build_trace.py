"""Private archive replacement: analysis trace conversion with explicit NET state."""
import json,shlex,shutil,subprocess,hashlib
from pathlib import Path
root=Path.cwd();shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';out=root/'build/native_search_seed_trace_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text()); original={p:sha(p) for p in protocol['inputs_sha256']}
read=(shared/'vpr/src/base/read_route.cpp').read_text();needle='route_ctx.route_trees[inet] = TracebackCompat::traceback_to_route_tree(head_ptr);';assert read.count(needle)==1
read=read.replace(needle,'routecast_import_net = inet;\n    '+needle+'\n    routecast_import_net = ParentNetId::INVALID();');read='extern thread_local ParentNetId routecast_import_net;\n'+read if False else read
# Declare after includes, where ParentNetId is visible.
read=read.replace('bool read_route(', 'extern thread_local ParentNetId routecast_import_net;\n\nbool read_route(',1)
old=(shared/'vpr/src/base/old_traceback.cpp').read_text();old=old.replace('/** Build a route tree from a traceback */','thread_local ParentNetId routecast_import_net = ParentNetId::INVALID();\n\n/** Build a route tree from a traceback */',1)
old=old.replace('RouteTree tree(RRNodeId(head->index));','RouteTree tree = routecast_import_net.is_valid() ? RouteTree(routecast_import_net) : RouteTree(RRNodeId(head->index));\n    if (routecast_import_net.is_valid() && tree.root().inode != RRNodeId(head->index)) throw std::runtime_error("seed SOURCE mismatch");')
old=old.replace('tree.add_node(parent, new_node);\n    new_node->net_pin_index = trace->net_pin_index;','new_node->net_pin_index = trace->net_pin_index;\n    if (tree._net_id.is_valid() && new_node->net_pin_index > 0) {\n        int pin = new_node->net_pin_index;\n        if (size_t(pin) > tree._num_sinks || tree._is_isink_reached.get(pin) || g_vpr_ctx.routing().net_rr_terminals[tree._net_id][pin] != inode) throw std::runtime_error("invalid imported sink identity");\n        tree._is_isink_reached.set(pin, true);\n    }\n    tree.add_node(parent, new_node);')
old='#include <stdexcept>\n'+old
(src/'read_route.cpp').write_text(read);(src/'old_traceback.cpp').write_text(old);shutil.copyfile(root/'tools/native_seed_import/hook.cpp',src/'hook.cpp');shutil.copyfile(__file__,src/'build.py')
compilebase=protocol['compile'][:-4] # drop -c source -o object
route=(shared/'vpr/src/route/route.cpp').read_text()
route='#include <cstdlib>\n#include <stdexcept>\n'+route
needle="""    init_route_structs(net_list,
                       router_opts.bb_factor,
                       router_opts.has_choke_point,
                       is_flat);"""
assert route.count(needle)==1
route=route.replace(needle,needle+"""
    const char* routecast_seed = std::getenv("ROUTECAST_NATIVE_SEED");
    if (routecast_seed && *routecast_seed) {
        if (is_flat) throw std::runtime_error("search seed rejects flat mode");
        bool feasible = read_route(routecast_seed, router_opts, true, is_flat);
        VTR_LOG("ROUTECAST NET-aware seed imported feasible=%d with actual router options\\n", int(feasible));
    }
""")
needle='        //Run STA to get estimated criticalities'
assert route.count(needle)==1
route=route.replace(needle,"""        if (routecast_seed && *routecast_seed) {
            for (auto net : net_list.nets()) {
                if (!route_ctx.route_trees[net]) continue;
                const auto& tree = route_ctx.route_trees[net].value();
                for (size_t pin=1; pin<net_list.net_pins(net).size(); ++pin) {
                    auto sink = tree.find_by_isink(pin);
                    if (!sink) throw std::runtime_error("incomplete seed delay map");
                    net_delay[net][pin] = sink->Tdel;
                }
            }
            VTR_LOG("ROUTECAST initialized net_delay from seed before STA\\n");
        }
"""+needle)
(src/'route.cpp').write_text(route)
net=(shared/'vpr/src/route/route_net.cpp').read_text()
needle='    bool ripup_high_fanout_nets = check_hold(router_opts, worst_neg_slack);'
assert net.count(needle)==1
net=net.replace(needle,"""    if (std::getenv("ROUTECAST_NATIVE_SEED")) {
        size_t nodes=0, overused=0, forced=0;
        if (tree) for (const auto& n : tree->all_nodes()) {
            ++nodes;
            if (route_ctx.rr_node_route_inf[n.inode].occ() > g_vpr_ctx.device().rr_graph.node_capacity(n.inode)) ++overused;
            if (n.is_leaf() && connections_inf.should_force_reroute_connection(net_id,n.inode)) ++forced;
        }
        VTR_LOG("ROUTECAST_SELECT iter=%d net=%zu nodes=%zu overused=%zu forced=%zu fanout=%zu first=%d lowfanout=%d hold=%d\\n",itry,size_t(net_id),nodes,overused,forced,net_list.net_sinks(net_id).size(),int(itry==1),int(net_list.net_sinks(net_id).size()<size_t(router_opts.min_incremental_reroute_fanout)),int(check_hold(router_opts,worst_neg_slack)));
    }
"""+needle)
net='#include <cstdlib>\n'+net
(src/'route_net.cpp').write_text(net)
objects=[]
for n in ('read_route','old_traceback','route','route_net'):
 obj=out/(n+'.o');cmd=[*compilebase,'-I'+str(shared/'vpr/src/base'),'-c',str(src/(n+'.cpp')),'-o',str(obj)]
 with (out/(n+'.log')).open('w') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 if result.returncode:raise SystemExit(n+' failed')
 objects.append(str(obj))
archive=out/'libvpr.a';shutil.copyfile(shared/'build_tileplace_vpr/vpr/libvpr.a',archive);subprocess.run(['ar','d',str(archive),'read_route.cpp.o','old_traceback.cpp.o','route.cpp.o','route_net.cpp.o'],check=True)
link=protocol['link'];link=[str(archive) if p.endswith('/libvpr.a') else str(out/'routecast_search_seed_vpr') if p.endswith('/routecast_seed_vpr') else p for p in link];link=[p for p in link if not p.endswith('/hook.o') and not p.startswith('-Wl,--wrap=')];link[1:1]=objects
with (out/'link.log').open('w') as f:res=subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,timeout=120)
assert all(sha(p)==h for p,h in original.items())
(out/'receipt.json').write_text(json.dumps({'exit_code':res.returncode,'shared_inputs_sha256':original,'sources_sha256':{str(p):sha(p) for p in src.iterdir()},'binary_sha256':sha(out/'routecast_search_seed_vpr') if res.returncode==0 else None,'scope':'Private read_route/traceback object replacement; explicit NET constructor and sink tables. Importer factors remain prototype constants.'},indent=2)+'\n');print(res.returncode)
