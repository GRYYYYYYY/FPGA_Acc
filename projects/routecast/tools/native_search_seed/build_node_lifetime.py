"""Private archive replacement: analysis trace conversion with explicit NET state."""
import json,shlex,shutil,subprocess,hashlib
from pathlib import Path
root=Path.cwd();shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';out=root/'build/native_seed_node_lifetime_v2_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protocol=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text()); original={p:sha(p) for p in protocol['inputs_sha256']}
read=(shared/'vpr/src/base/read_route.cpp').read_text();needle='route_ctx.route_trees[inet] = TracebackCompat::traceback_to_route_tree(head_ptr);';assert read.count(needle)==1
read=read.replace(needle,'routecast_import_net = inet;\n    '+needle+'\n    routecast_import_net = ParentNetId::INVALID();');read='extern thread_local ParentNetId routecast_import_net;\n'+read if False else read
# Declare after includes, where ParentNetId is visible.
read=read.replace('bool read_route(', 'extern thread_local ParentNetId routecast_import_net;\n\nbool read_route(',1)
old=(shared/'vpr/src/base/old_traceback.cpp').read_text();old=old.replace('/** Build a route tree from a traceback */','thread_local ParentNetId routecast_import_net = ParentNetId::INVALID();\n\n/** Build a route tree from a traceback */',1)
old=old.replace('RouteTree tree(RRNodeId(head->index));','RouteTree tree = routecast_import_net.is_valid() ? RouteTree(routecast_import_net) : RouteTree(RRNodeId(head->index));\n    if (routecast_import_net.is_valid() && tree.root().inode != RRNodeId(head->index)) throw std::runtime_error("seed SOURCE mismatch");')
old=old.replace('tree.add_node(parent, new_node);\n    new_node->net_pin_index = trace->net_pin_index;','new_node->net_pin_index = trace->net_pin_index;\n    if (tree._net_id.is_valid() && new_node->net_pin_index > 0) {\n        int pin = new_node->net_pin_index;\n        if (size_t(pin) > tree._num_sinks || tree._is_isink_reached.get(pin) || g_vpr_ctx.routing().net_rr_terminals[tree._net_id][pin] != inode) throw std::runtime_error("invalid imported sink identity");\n        tree._is_isink_reached.set(pin, true);\n    }\n    tree.add_node(parent, new_node);')
old='#include <stdexcept>\n#include \"vpr_error.h\"\n'+old
old=old.replace('throw std::runtime_error(\"seed SOURCE mismatch\")','vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,\"seed SOURCE mismatch\")').replace('throw std::runtime_error(\"invalid imported sink identity\")','vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,\"invalid imported sink identity\")')
read='#include <tuple>\n'+read
read=read.replace('bool read_route(', 'static bool routecast_read_unchecked(',1)
read+='\nbool read_route(const char* path,const t_router_opts& opts,bool digests,bool flat) {\n auto& ctx=g_vpr_ctx.mutable_routing();\n auto saved=std::make_tuple(std::move(ctx.route_trees),ctx.trace_nodes,ctx.net_rr_terminals,ctx.is_clock_net,ctx.rr_blk_source,ctx.rr_node_route_inf,ctx.net_terminal_groups,ctx.net_terminal_group_num,ctx.non_configurable_bitset,ctx.net_status,ctx.route_bb,ctx.clb_opins_used_locally,ctx.routing_id,ctx.is_flat);\n auto old_import_net=routecast_import_net;\n try { return routecast_read_unchecked(path,opts,digests,flat); }\n catch (...) {\n  std::swap(ctx.route_trees,std::get<0>(saved));\n  std::swap(ctx.trace_nodes,std::get<1>(saved));\n  std::swap(ctx.net_rr_terminals,std::get<2>(saved));\n  std::swap(ctx.is_clock_net,std::get<3>(saved));\n  std::swap(ctx.rr_blk_source,std::get<4>(saved));\n  std::swap(ctx.rr_node_route_inf,std::get<5>(saved));\n  std::swap(ctx.net_terminal_groups,std::get<6>(saved));\n  std::swap(ctx.net_terminal_group_num,std::get<7>(saved));\n  std::swap(ctx.non_configurable_bitset,std::get<8>(saved));\n  std::swap(ctx.net_status,std::get<9>(saved));\n  std::swap(ctx.route_bb,std::get<10>(saved));\n  std::swap(ctx.clb_opins_used_locally,std::get<11>(saved));\n  std::swap(ctx.routing_id,std::get<12>(saved));\n  std::swap(ctx.is_flat,std::get<13>(saved));\n  routecast_import_net=old_import_net;\n  throw;\n }\n}\n'
read='#include <type_traits>\n#include <cstdlib>\n'+read
start=read.index(' auto saved=std::make_tuple(')
end=read.index(';',start)
fields=['trace_nodes','net_rr_terminals','is_clock_net','rr_blk_source','rr_node_route_inf','net_terminal_groups','net_terminal_group_num','non_configurable_bitset','net_status','route_bb','clb_opins_used_locally','routing_id','is_flat']
replacement=""" int copy_index=0;
 auto capture=[&](const auto& value) {
     ++copy_index;
     if (const char* fail=std::getenv("ROUTECAST_SNAPSHOT_FAIL")) {
         if (std::atoi(fail)==copy_index) vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,"injected snapshot copy failure %d",copy_index);
     }
     return value;
 };
 auto saved=std::make_tuple(decltype(ctx.route_trees){},"""+','.join('capture(ctx.'+f+')' for f in fields)+""");
 static_assert(noexcept(std::swap(ctx.route_trees,std::get<0>(saved))),"tree transfer must not throw");
 std::swap(ctx.route_trees,std::get<0>(saved))"""
read=read[:start]+replacement+read[end:]
helper="""static void routecast_late_failure(int stage) {
    if (const char* fail=std::getenv("ROUTECAST_IMPORT_FAIL")) {
        if (std::atoi(fail)==stage) {
            VTR_LOG("ROUTECAST injected late import failure stage=%d\\n",stage);
            vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,"injected late import failure %d",stage);
        }
    }
}
"""
read=read.replace('static bool routecast_read_unchecked(',helper+'static bool routecast_read_unchecked(',1)
needle='    recompute_occupancy_from_scratch(router_net_list,\n                                     flat_router);'
assert read.count(needle)==2
read=read.replace(needle,needle+'\n    routecast_late_failure(1);',1)
read=read.replace('    pathfinder_update_acc_cost_and_overuse_info(router_opts.acc_fac, overuse_info);','    pathfinder_update_acc_cost_and_overuse_info(router_opts.acc_fac, overuse_info);\n    routecast_late_failure(2);',1)
read=read.replace('router_opts.acc_fac, true, flat_router);','router_opts.acc_fac, true, flat_router);\n        routecast_late_failure(3);',1)
# Find the remaining last occupancy recomputation, after final check comment.
needle='    bool is_feasible = feasible_routing();'
read=read.replace(needle,'    routecast_late_failure(4);\n'+needle,1)
read=read.replace('    t_trace* head_ptr = nullptr;',"""    t_trace* head_ptr = nullptr;
    struct TraceGuard {
        t_trace*& head;
        ~TraceGuard() { free_traceback(head); }
    } trace_guard{head_ptr};""",1)
assert read.count('    free_traceback(head_ptr);')==1
read=read.replace('    free_traceback(head_ptr);','    // TraceGuard releases parsed traceback on success and every exception.',1)
# Check every restore swap at compile time, before any context mutation.
fields=['route_trees','trace_nodes','net_rr_terminals','is_clock_net','rr_blk_source','rr_node_route_inf','net_terminal_groups','net_terminal_group_num','non_configurable_bitset','net_status','route_bb','clb_opins_used_locally','routing_id','is_flat']
for i,f in enumerate(fields):
 stmt=f'  std::swap(ctx.{f},std::get<{i}>(saved));'
 assert stmt in read
 read=read.replace(stmt,f'  static_assert(noexcept(std::swap(ctx.{f},std::get<{i}>(saved))),"restore {f} must not throw");\n'+stmt,1)
# Reject sink identity before allocating an unattached node.
a=old.index('    RouteTreeNode* new_node = new RouteTreeNode(inode, parent_switch, parent);')
b=old.index('    tree.add_node(parent, new_node);',a)
block=old[a:b]
allocation='    RouteTreeNode* new_node = new RouteTreeNode(inode, parent_switch, parent);\n    new_node->net_pin_index = trace->net_pin_index;\n'
assert allocation in block
validation=block.replace(allocation,'').replace('new_node->net_pin_index','trace->net_pin_index')
old=old[:a]+validation+allocation+old[b:]
(src/'read_route.cpp').write_text(read);old='long routecast_live_traces=0;\n'+old
needle='    return (t_trace*)malloc(sizeof(t_trace));'
assert old.count(needle)==1
old=old.replace(needle,'    auto* p=(t_trace*)malloc(sizeof(t_trace)); if(p) ++routecast_live_traces; return p;',1)
old=old.replace('    free(tptr);','    if(tptr) --routecast_live_traces;\n    free(tptr);',1)
old='extern void routecast_track_import_node(const void*);\n'+old
old=old.replace('    if (routecast_import_net.is_valid() && tree.root().inode', '    routecast_track_import_node(&tree.root());\n    if (routecast_import_net.is_valid() && tree.root().inode',1)
old=old.replace('    new_node->net_pin_index = trace->net_pin_index;', '    routecast_track_import_node(new_node);\n    new_node->net_pin_index = trace->net_pin_index;',1)
shutil.copyfile(root/'tools/native_node_lifetime/tracker.cpp',src/'tracker.cpp')
(src/'old_traceback.cpp').write_text(old);shutil.copyfile(root/'tools/native_seed_import/hook.cpp',src/'hook.cpp');shutil.copyfile(__file__,src/'build.py')
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
# Populate imported delays also when LOOKAHEAD initialization is not selected.
marker='    /* Get initial criticalities from the lookahead */'
assert route.count(marker)==1
route=route.replace(marker,"""    if (routecast_seed && *routecast_seed && router_opts.initial_timing != e_router_initial_timing::LOOKAHEAD) {
        for (auto net : net_list.nets()) {
            if (!route_ctx.route_trees[net]) continue;
            const auto& tree = route_ctx.route_trees[net].value();
            for (size_t pin=1; pin<net_list.net_pins(net).size(); ++pin) {
                auto sink = tree.find_by_isink(pin);
                if (!sink) throw std::runtime_error("incomplete seed delay map");
                net_delay[net][pin] = sink->Tdel;
            }
        }
        VTR_LOG("ROUTECAST initialized seed delays for non-lookahead timing\\n");
    }
"""+marker)
route='#include <fstream>\n#include <iomanip>\n#include \"vpr_error.h\"\n'+route
route=route.replace('bool route(', 'void print_route(const Netlist<>&, FILE*, bool);\n\nbool route(',1)
marker='    IntraLbPbPinLookup intra_lb_pb_pin_lookup'
assert route.count(marker)==1
route=route.replace(marker,'\n    if (const char* bad=std::getenv("ROUTECAST_BAD_IMPORT")) {\n        auto dump=[&](const char* prefix) {\n            std::string trace=std::string(prefix)+".route";\n            FILE* f=std::fopen(trace.c_str(),"w");\n            if (!f) throw std::runtime_error("probe file open");\n            print_route(net_list,f,is_flat);std::fclose(f);\n            std::ofstream info(std::string(prefix)+".nodes");info<<std::setprecision(17);\n            for (const auto& n:route_ctx.rr_node_route_inf) info<<n.occ()<<" "<<n.acc_cost<<" "<<n.path_cost<<" "<<n.backward_path_cost<<"\\n";\n        };\n        dump("before_bad");bool rejected=false;\n        if (const char* probe=std::getenv("ROUTECAST_COPY_PROBE")) setenv("ROUTECAST_SNAPSHOT_FAIL",probe,1); if (const char* late=std::getenv("ROUTECAST_LATE_PROBE")) setenv("ROUTECAST_IMPORT_FAIL",late,1); try { read_route(bad,router_opts,true,is_flat); }\n        catch (const VprError&) { rejected=true; } unsetenv("ROUTECAST_SNAPSHOT_FAIL"); unsetenv("ROUTECAST_IMPORT_FAIL");\n        if (!rejected) throw std::runtime_error("bad import unexpectedly accepted");\n        dump("after_bad");\n        VTR_LOG("ROUTECAST bad import rejected and routing snapshot restored\\n");\n    }\n'+marker)
route='#include <malloc.h>\nextern long routecast_live_traces;\n'+route
needle='try { read_route(bad,router_opts,true,is_flat); }\n        catch (const VprError&) { rejected=true; }'
assert route.count(needle)==1
route=route.replace(needle,"""long baseline_traces=routecast_live_traces;
        for (int repetition=0; repetition<100; ++repetition) {
            bool caught=false;
            try { read_route(bad,router_opts,true,is_flat); }
            catch (const VprError&) { caught=true; rejected=true; }
            if (!caught || routecast_live_traces!=baseline_traces) throw std::runtime_error("repeat rejection or traceback allocation imbalance");
            if (repetition%10==0 || repetition==99) {
                auto memory=mallinfo2();
                VTR_LOG("ROUTECAST_REPEAT count=%d trace_live=%ld allocator_used=%zu allocator_mmap=%zu\\n",repetition+1,routecast_live_traces,size_t(memory.uordblks),size_t(memory.hblkhd));
            }
        }
""")
route='extern long routecast_live_import_nodes;\n'+route
route=route.replace('long baseline_traces=routecast_live_traces;','long baseline_traces=routecast_live_traces;long baseline_nodes=routecast_live_import_nodes;')
route=route.replace('routecast_live_traces!=baseline_traces','routecast_live_traces!=baseline_traces || routecast_live_import_nodes!=baseline_nodes')
route=route.replace('allocator_mmap=%zu\\n','allocator_mmap=%zu import_nodes=%ld\\n').replace('size_t(memory.hblkhd));','size_t(memory.hblkhd),routecast_live_import_nodes);')
(src/'route.cpp').write_text(route)
objects=[]
for n in ('read_route','old_traceback','route','tracker'):
 obj=out/(n+'.o');cmd=[*compilebase,'-I'+str(shared/'vpr/src/base'),'-c',str(src/(n+'.cpp')),'-o',str(obj)]
 with (out/(n+'.log')).open('w') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 if result.returncode:raise SystemExit(n+' failed')
 objects.append(str(obj))
archive=out/'libvpr.a';shutil.copyfile(shared/'build_tileplace_vpr/vpr/libvpr.a',archive);subprocess.run(['ar','d',str(archive),'read_route.cpp.o','old_traceback.cpp.o','route.cpp.o'],check=True)
link=protocol['link'];link=[str(archive) if p.endswith('/libvpr.a') else str(out/'routecast_search_seed_vpr') if p.endswith('/routecast_seed_vpr') else p for p in link];link=[p for p in link if not p.endswith('/hook.o') and not p.startswith('-Wl,--wrap=')];link[1:1]=objects+['-Wl,--wrap=_ZdlPv','-Wl,--wrap=_ZdlPvm']
with (out/'link.log').open('w') as f:res=subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,timeout=120)
assert all(sha(p)==h for p,h in original.items())
(out/'receipt.json').write_text(json.dumps({'exit_code':res.returncode,'shared_inputs_sha256':original,'sources_sha256':{str(p):sha(p) for p in src.iterdir()},'binary_sha256':sha(out/'routecast_search_seed_vpr') if res.returncode==0 else None,'scope':'Private read_route/traceback object replacement; explicit NET constructor and sink tables. Importer factors remain prototype constants.'},indent=2)+'\n');print(res.returncode)
