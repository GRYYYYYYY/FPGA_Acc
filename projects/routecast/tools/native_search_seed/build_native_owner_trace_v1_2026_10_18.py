"""Isolated serial-native read-only owner/reason/checkpoint observer build."""
import json,sys,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
B=R/'build/native_partial_net_firstpass_v1_2026-10-18';bp=B/'receipt.json';b=json.loads(bp.read_text());assert sha(B/'sequence_vpr')==b['binary_sha256'] and all(sha(p)==h for p,h in b['bindings'].items());D=R/'build/native_owner_trace_v1_2026-10-18';templates=R/'tools/native_search_seed/owner_trace_v1_2026_10_18';old=B/'source/route.cpp';original=old.read_text();text=original;route_edits=[]
def edit(a,z,one=False):
 global text
 assert a in text and (one or text.count(a)==1),a
 text=text.replace(a,z,1);route_edits.append((a,z))
edit('#include "vtr_time.h"','#include "vtr_time.h"\n#include "routecast_owner_trace.h"')
a='    IntraLbPbPinLookup intra_lb_pb_pin_lookup(device_ctx.logical_block_types);'
z='''    if(const char* trace=std::getenv("ROUTECAST_NATIVE_OWNER_TRACE")) {
        if(*trace && (is_flat || retained_input || !routecast_seed || !*routecast_seed || router_opts.initial_timing!=e_router_initial_timing::LOOKAHEAD || router_opts.router_algorithm!=e_router_algorithm::TIMING_DRIVEN))
            throw std::runtime_error("owner observer requires serial LOOKAHEAD file-seed routing");
    }
    routecast_trace_begin(net_list);
'''+a
edit(a,z,True)
a='        RouteIterResults iter_results = netlist_router->route_netlist(itry, pres_fac, worst_negative_slack);';edit(a,'        routecast_trace_iter_begin(itry,net_list);\n'+a+'\n        routecast_trace_routed(net_list);')
a='        print_route_status(itry, iter_elapsed_time, pres_fac, num_net_bounding_boxes_updated, iter_results.stats, overuse_info, wirelength_info, timing_info, est_success_iteration);';edit(a,'        routecast_trace_iter_end(itry,net_list,iter_results.stats);\n'+a)
edit('    return success;','    routecast_trace_finish(net_list,success);\n    return success;')
check=text
for a,z in reversed(route_edits):check=check.replace(z,a,1)
assert check==original
oldnet=B/'source/route_net.cpp';original_net=oldnet.read_text();net=original_net;net_edits=[]
def ne(a,z):
 global net
 assert net.count(a)==1,a
 net=net.replace(a,z);net_edits.append((a,z))
ne('#include "stats.h"','#include "stats.h"\n#include "routecast_owner_trace_impl.h"')
a='    if ((!routecast_preserve && (num_sinks < router_opts.min_incremental_reroute_fanout || itry == 1)) || ripup_high_fanout_nets) {';ne(a,'    routecast_trace_setup(itry,net_id,routecast_preserve,ripup_high_fanout_nets);\n'+a)
sub_start=net.index('bool should_route_net(');sub_end=net.index('\nbool early_exit_heuristic',sub_start);sub=net[sub_start:sub_end];oldsub=sub;subedits=[]
def se(a,z):
 global sub
 assert sub.count(a)==1,a
 sub=sub.replace(a,z);subedits.append((a,z))
se('    auto& route_ctx = g_vpr_ctx.routing();','    routecast_trace_decision_enter();\n    auto& route_ctx = g_vpr_ctx.routing();')
for anchor,reason in [('    if (!route_ctx.route_trees[net_id]) /* No routing yet */\n        return true;','missing_tree'),('    if (worst_negative_slack != 0 && budgeting_inf.if_set() && budgeting_inf.get_should_reroute(net_id)) /* Reroute for hold */\n        return true;','hold_force')]:
 replacement=anchor.split('\n')[0]+' {\n        routecast_trace_decision(net_id,"'+reason+'");\n        return true;\n    }';se(anchor,replacement)
se('            return true; /* overuse detected */','            routecast_trace_decision(net_id,"overuse",inode);\n            return true; /* overuse detected */')
se('                    return true;','                    routecast_trace_decision(net_id,"forced_connection",inode);\n                    return true;')
se('    return true;\n}','    routecast_trace_decision(net_id,"remaining_sinks");\n    return true;\n}')
net=net[:sub_start]+sub+net[sub_end:];checksub=sub
for x,y in reversed(subedits):checksub=checksub.replace(y,x,1)
assert checksub==oldsub
checknet=net.replace(sub,oldsub,1)
for x,y in reversed(net_edits):checknet=checknet.replace(y,x,1)
assert checknet==original_net
D.mkdir();src=D/'source';src.mkdir()
for name,content in [('route.cpp',text),('route_net.cpp',net)]:
 with (src/name).open('x') as f:f.write(content)
for name in ['routecast_owner_trace.h','routecast_owner_trace_impl.h']:shutil.copyfile(templates/name,src/name)
shutil.copyfile(__file__,src/'build.py');proto=B/'protocol.json';P=json.loads(proto.read_text());compiles=[[*P['compile'][:-4],'-c',str(src/name),'-o',str(D/obj)] for name,obj in [('route.cpp','route.o'),('route_net.cpp','route_net.o')]];link=[x.replace(str(B)+'/',str(D)+'/') for x in P['link']];bindings={**b['bindings'],**closure([Path(__file__)]),str(bp):sha(bp),str(proto):sha(proto),**{str(p):sha(p) for p in templates.iterdir() if p.is_file()},**{str(p):sha(p) for p in src.iterdir() if p.is_file()}}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,compile=compiles,link=link,base_binary_sha256=b['binary_sha256'],route_hook_edits=route_edits,route_net_hook_edits=net_edits,decision_hook_edits=subedits,source_removal_recovers_original_route_and_route_net_exactly=True,scope='Opt-in read-only serial native observer. No runtime equivalence or event completeness claimed until actual validation.'),f,indent=2)
for index,cmd in enumerate(compiles):
 print('OWNER OBSERVER COMPILE',index,flush=True)
 with (D/('compile'+str(index)+'.log')).open('x') as f:subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=None)
print('OWNER OBSERVER LINK',flush=True)
with (D/'link.log').open('x') as f:subprocess.run(link,cwd=R,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=None)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},binary_sha256=sha(D/'sequence_vpr'),read_only_hooks_original_routing_source_recovered_exactly=True,runtime_equivalence_pending=True,all6_matched_jobs_pending=True,independent_trace_replay_pending=True),f,indent=2)
print('OWNER OBSERVER BUILD PASS',flush=True)
