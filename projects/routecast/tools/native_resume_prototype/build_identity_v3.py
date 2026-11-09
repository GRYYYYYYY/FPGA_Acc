"""Compile two private source copies and replace objects in private libvpr."""
import json,shlex,shutil,subprocess,time
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];up=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';build=up/'build_tileplace_vpr/vpr'
out=ROOT/'build/native_resume_identity_v3_2026-10-07';out.mkdir(exist_ok=False);(out/'source').mkdir()
files=[up/'vpr/src/route/route.cpp',up/'vpr/src/route/route_net.cpp'];original={str(p):sha(p) for p in files}
a=files[0].read_text();a='#include <cstdlib>\n#include "net_delay.h"\n'+a
needle='    CBRR connections_inf{net_list, route_ctx.net_rr_terminals, is_flat};'
insert='''    const char* routecast_seed = std::getenv("ROUTECAST_RESUME_SAME_PLACE_ROUTE");
    if (routecast_seed) {
        if (is_flat || !router_opts.with_timing_analysis || router_opts.initial_timing != e_router_initial_timing::LOOKAHEAD)
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "RouteCast same-place resume requires clustered timing/lookahead mode");
        if (!read_route(routecast_seed, router_opts, true, is_flat))
            VPR_FATAL_ERROR(VPR_ERROR_ROUTE, "RouteCast seed is infeasible");
        size_t loaded = 0;
        for (auto net : net_list.nets()) if (route_ctx.route_trees[net]) ++loaded;
        VTR_LOG("ROUTECAST_RESUME_LOADED_TREES %zu\\n", loaded);
        load_net_delay_from_routing(net_list, net_delay);
        timing_info->update();
    }
'''
assert a.count(needle)==1;a=a.replace(needle,insert+needle)
needle='if (router_opts.with_timing_analysis && router_opts.initial_timing == e_router_initial_timing::LOOKAHEAD)'
assert a.count(needle)==1;a=a.replace(needle,'if (!routecast_seed && router_opts.with_timing_analysis && router_opts.initial_timing == e_router_initial_timing::LOOKAHEAD)')
b='#include <cstdlib>\n'+files[1].read_text()
needle='if (num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1 || ripup_high_fanout_nets)'
replacement='''const bool routecast_keep_first = std::getenv("ROUTECAST_RESUME_SAME_PLACE_ROUTE") && itry == 1 && tree;
    if (routecast_keep_first) VTR_LOG("ROUTECAST_RESUME_FIRST_TREE %zu\\n", size_t(net_id));
    if ((!routecast_keep_first && (num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1)) || ripup_high_fanout_nets)'''
assert b.count(needle)==1;b=b.replace(needle,replacement)

base=up/'vpr/src/base'
for file in (base/'old_traceback.cpp',base/'old_traceback.h',base/'read_route.cpp'): original[str(file)]=sha(file)
header=(base/'old_traceback.h').read_text()
header=header.replace('    static vtr::optional<RouteTree> traceback_to_route_tree(t_trace* head);','    static vtr::optional<RouteTree> traceback_to_route_tree(t_trace* head);\n    static vtr::optional<RouteTree> traceback_to_route_tree(t_trace* head, ParentNetId net);')
(out/'source/old_traceback.h').write_text(header)
trace=(base/'old_traceback.cpp').read_text()
marker='/* Add the path indicated by the trace to parent */'
extra=r"""
vtr::optional<RouteTree> TracebackCompat::traceback_to_route_tree(t_trace* head, ParentNetId net) {
    if (!head) return vtr::nullopt;
    RouteTree tree(net);
    if (tree.root().inode != RRNodeId(head->index)) throw std::runtime_error("Resume SOURCE mismatch");
    if (head->next) traceback_to_route_tree_x(head->next, tree, tree._root, RRSwitchId(head->iswitch));
    for (auto& node : tree.all_nodes()) {
        if (g_vpr_ctx.device().rr_graph.node_type(node.inode) != SINK) continue;
        int pin = node.net_pin_index;
        if (pin < 1 || size_t(pin) > tree._num_sinks || tree._isink_to_rt_node[pin-1])
            throw std::runtime_error("Resume invalid/duplicate sink pin");
        if (node.inode != g_vpr_ctx.routing().net_rr_terminals[net][pin])
            throw std::runtime_error("Resume sink terminal mismatch");
        // all_nodes exposes const references to nodes owned by this mutable tree.
        tree._isink_to_rt_node[pin-1] = const_cast<RouteTreeNode*>(&node);
        tree._is_isink_reached.set(pin, true);
    }
    for (size_t pin=1; pin<=tree._num_sinks; ++pin)
        if (!tree._is_isink_reached.get(pin)) throw std::runtime_error("Resume incomplete NET");
    tree.reload_timing();
    return tree;
}
"""
trace='#include <stdexcept>\n'+trace.replace(marker,extra+'\n'+marker)
reader='#include <cstdlib>\n'+(base/'read_route.cpp').read_text()
reader=reader.replace('route_ctx.route_trees[inet] = TracebackCompat::traceback_to_route_tree(head_ptr);','route_ctx.route_trees[inet] = std::getenv("ROUTECAST_RESUME_SAME_PLACE_ROUTE") ? TracebackCompat::traceback_to_route_tree(head_ptr, inet) : TracebackCompat::traceback_to_route_tree(head_ptr);')
flags={}
for line in (build/'CMakeFiles/libvpr.dir/flags.make').read_text().splitlines():
 if ' = ' in line:k,v=line.split(' = ',1);flags[k]=shlex.split(v)
archive=build/'libvpr.a';original[str(archive)]=sha(archive);private=out/'libvpr.a'
commands=[]
for name,text in [('route.cpp',a),('route_net.cpp',b),('old_traceback.cpp',trace),('read_route.cpp',reader)]:
 source=out/'source'/name;source.write_text(text)
 commands.append(['/usr/bin/c++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],'-c',str(source),'-o',str(out/(name+'.o'))])
link=shlex.split((build/'CMakeFiles/vpr.dir/link.txt').read_text());exe=out/'routecast_resume_vpr'
link=[str(exe) if x=='vpr' else str(private) if x=='libvpr.a' else str((build/x).resolve()) if x.endswith(('.a','.o')) else x for x in link]
# CMake may spell the local archive with a path prefix.
link=[str(private) if x==str(archive) else x for x in link];assert str(private) in link
for x in link:
 if x.endswith(('.a','.o')) and x!=str(private):original[x]=sha(x)
protocol=dict(original_inputs=original,sources={str(out/'source'/n):sha(out/'source'/n) for n in ('route.cpp','route_net.cpp','old_traceback.cpp','read_route.cpp','old_traceback.h')},builder_sha256=sha(Path(__file__)),compile=commands,link=link,scope='Prototype same-placement only, not target conversion or proven resume; shared source/archive read only')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter()
for i,command in enumerate(commands):
 with (out/f'compile{i}.log').open('w') as log:
  result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 if result.returncode:raise SystemExit(result.returncode)
shutil.copyfile(archive,private)
for command in (['/usr/bin/ar','r',str(private),str(out/'route.cpp.o'),str(out/'route_net.cpp.o'),str(out/'old_traceback.cpp.o'),str(out/'read_route.cpp.o')],['/usr/bin/ranlib',str(private)],link):
 with (out/'link.log').open('a') as log:result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
 if result.returncode:raise SystemExit(result.returncode)
assert all(sha(p)==h for p,h in original.items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),binary_sha256=sha(exe),private_archive_sha256=sha(private),build_seconds=time.perf_counter()-start,original_inputs_unchanged=True,behavior_verified=False),indent=2)+'\n');print(exe)
