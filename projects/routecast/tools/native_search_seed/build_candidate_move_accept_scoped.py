"""Private archive replacement: analysis trace conversion with explicit NET state."""
import json,shlex,shutil,subprocess,hashlib
from pathlib import Path
root=Path.cwd();shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';out=root/'build/native_candidate_move_accept_scoped_2026-10-06';out.mkdir();src=out/'source';src.mkdir()
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
route='#include "RoutingDelayCalculator.h"\n#include "vpr_error.h"\n#include <tuple>\n'+route
marker='    std::unique_ptr<NetlistRouter> netlist_router = make_netlist_router('
assert route.count(marker)==1
probe="""    if (std::getenv("ROUTECAST_TIMING_RESTORE_PROBE")) {
        auto refresh=[&]() {
            delay_calc->clear_cache();
            for(auto edge:g_vpr_ctx.timing().graph->edges())timing_info->invalidate_delay(edge);
            timing_info->update();
        };
        auto metrics=[&]() {return std::make_tuple(timing_info->least_slack_critical_path().delay(),timing_info->setup_total_negative_slack(),timing_info->setup_worst_negative_slack());};
        auto edges=[&]() {
            std::vector<std::pair<float,float>> result;
            for(auto edge:g_vpr_ctx.timing().graph->edges()) { const auto& graph=*g_vpr_ctx.timing().graph; if(graph.edge_type(edge)==tatum::EdgeType::PRIMITIVE_CLOCK_CAPTURE)result.emplace_back(float(delay_calc->setup_time(graph,edge)),float(delay_calc->hold_time(graph,edge))); else result.emplace_back(float(delay_calc->max_edge_delay(graph,edge)),float(delay_calc->min_edge_delay(graph,edge))); }
            return result;
        };
        refresh();auto before=metrics();auto before_edges=edges();
        std::vector<std::tuple<ParentNetId,size_t,float>> saved;
        for(auto net:net_list.nets())for(size_t pin=1;pin<net_list.net_pins(net).size();++pin)saved.emplace_back(net,pin,net_delay[net][pin]);
        bool rejected=false;bool mutation=false;
        try {
            for(const auto& row:saved)net_delay[std::get<0>(row)][std::get<1>(row)]=std::get<2>(row)+1.e-9f;
            refresh();mutation=(metrics()!=before);
            VTR_LOG("ROUTECAST timing mutation observed=%d before_cpd_ns=%g candidate_cpd_ns=%g\\n",int(mutation),1.e9*std::get<0>(before),1.e9*std::get<0>(metrics()));
            vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,"injected failure after candidate STA");
        } catch(const VprError&) {
            rejected=true;
            for(const auto& row:saved)net_delay[std::get<0>(row)][std::get<1>(row)]=std::get<2>(row);
            refresh();
        }
        if(!rejected || !mutation || metrics()!=before || edges()!=before_edges)throw std::runtime_error("timing recovery mismatch");
        VTR_LOG("ROUTECAST restored delay matrix and all edge-delay/STA metric observations\\n");
    }
"""
route=route.replace(marker,probe+marker)
route='#include "post_routing_pb_pin_fixup.h"\n#include <type_traits>\n'+route
needle='        bool rejected=false;bool mutation=false;'
assert route.count(needle)==1
route=route.replace(needle,"""        std::vector<std::pair<t_pb*,t_pb>> pb_saved;
        auto collect=[&](auto&& self,t_pb* pb)->void {
            pb_saved.emplace_back(pb,*pb);
            if(pb->child_pbs)for(int t=0;t<pb->get_num_child_types();++t)for(int c=0;c<pb->get_num_children_of_type(t);++c)self(self,&pb->child_pbs[t][c]);
        };
        auto& mutable_cluster=g_vpr_ctx.mutable_clustering();
        auto& mutable_atom=g_vpr_ctx.mutable_atom();
        for(auto block:mutable_cluster.clb_nlist.blocks())collect(collect,mutable_cluster.clb_nlist.block_pb(block));
        auto saved_lookup=mutable_atom.lookup;
        auto saved_post=mutable_cluster.post_routing_clb_pin_nets;
        auto saved_pre=mutable_cluster.pre_routing_net_pin_mapping;
        bool rejected=false;bool mutation=false;
""")
needle='            refresh();mutation=(metrics()!=before);'
route=route.replace(needle,"""            bool quiet=false;
            sync_netlists_to_routing(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement(),quiet);
            VTR_LOG("ROUTECAST actual packing sync completed before timing failure\\n");
"""+needle,1)
needle='            for(const auto& row:saved)net_delay[std::get<0>(row)][std::get<1>(row)]=std::get<2>(row);'
route=route.replace(needle,"""            static_assert(std::is_nothrow_swappable<t_pb>::value,"pb restore");
            static_assert(std::is_nothrow_swappable<AtomLookup>::value,"lookup restore");
            for(auto& entry:pb_saved)std::swap(*entry.first,entry.second);
            std::swap(mutable_atom.lookup,saved_lookup);
            mutable_cluster.post_routing_clb_pin_nets.swap(saved_post);
            mutable_cluster.pre_routing_net_pin_mapping.swap(saved_pre);
"""+needle,1)
route='#include \"move_transactions.h\"\n'+route
route=route.replace('        bool rejected=false;bool mutation=false;','        auto routing_saved=std::make_tuple(decltype(route_ctx.route_trees){},route_ctx.trace_nodes,route_ctx.net_rr_terminals,route_ctx.is_clock_net,route_ctx.rr_blk_source,route_ctx.rr_node_route_inf,route_ctx.net_terminal_groups,route_ctx.net_terminal_group_num,route_ctx.non_configurable_bitset,route_ctx.net_status,route_ctx.route_bb,route_ctx.clb_opins_used_locally,route_ctx.routing_id,route_ctx.is_flat);\n        auto& registry=g_vpr_ctx.mutable_placement().mutable_blk_loc_registry();\n        auto old_a=registry.block_locs()[ClusterBlockId(0)].loc;\n        auto old_b=registry.block_locs()[ClusterBlockId(1)].loc;\n        if(device_ctx.grid.get_physical_type({old_a.x,old_a.y,old_a.layer})!=device_ctx.grid.get_physical_type({old_b.x,old_b.y,old_b.layer}) || old_a.sub_tile!=old_b.sub_tile || old_a.layer!=old_b.layer)throw std::runtime_error("candidate pair incompatible");\n        t_pl_blocks_to_be_moved exchange(2),reverse(2);\n        exchange.moved_blocks.emplace_back(ClusterBlockId(0),old_a,old_b);exchange.moved_blocks.emplace_back(ClusterBlockId(1),old_b,old_a);\n        reverse.moved_blocks.emplace_back(ClusterBlockId(0),old_b,old_a);reverse.moved_blocks.emplace_back(ClusterBlockId(1),old_a,old_b);\n        std::string original_seed=std::getenv("ROUTECAST_NATIVE_SEED");\n        std::swap(route_ctx.route_trees,std::get<0>(routing_saved));\n        bool placement_committed=false;\n'+'        bool rejected=false;bool mutation=false;',1)
route=route.replace('            for(const auto& row:saved)net_delay[std::get<0>(row)][std::get<1>(row)]=std::get<2>(row)+1.e-9f;','            registry.apply_move_blocks(exchange);registry.commit_move_blocks(exchange);placement_committed=true;\n            unsetenv("ROUTECAST_NATIVE_SEED");unsetenv("ROUTECAST_TIMING_RESTORE_PROBE");\n            bool candidate_ok=route(net_list,width_fac,router_opts,analysis_opts,det_routing_arch,segment_inf,net_delay,timing_info,delay_calc,chan_width_dist,directs,first_iteration_priority,is_flat);\n            if(!candidate_ok)vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,"candidate routing failed");\n            VTR_LOG("ROUTECAST actual moved candidate search completed before synchronization\\n");\n',1)
route=route.replace('            for(auto& entry:pb_saved)std::swap(*entry.first,entry.second);','            static_assert(noexcept(std::swap(route_ctx.route_trees,std::get<0>(routing_saved))),"restore route_trees");\n            std::swap(route_ctx.route_trees,std::get<0>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.trace_nodes,std::get<1>(routing_saved))),"restore trace_nodes");\n            std::swap(route_ctx.trace_nodes,std::get<1>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.net_rr_terminals,std::get<2>(routing_saved))),"restore net_rr_terminals");\n            std::swap(route_ctx.net_rr_terminals,std::get<2>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.is_clock_net,std::get<3>(routing_saved))),"restore is_clock_net");\n            std::swap(route_ctx.is_clock_net,std::get<3>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.rr_blk_source,std::get<4>(routing_saved))),"restore rr_blk_source");\n            std::swap(route_ctx.rr_blk_source,std::get<4>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.rr_node_route_inf,std::get<5>(routing_saved))),"restore rr_node_route_inf");\n            std::swap(route_ctx.rr_node_route_inf,std::get<5>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.net_terminal_groups,std::get<6>(routing_saved))),"restore net_terminal_groups");\n            std::swap(route_ctx.net_terminal_groups,std::get<6>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.net_terminal_group_num,std::get<7>(routing_saved))),"restore net_terminal_group_num");\n            std::swap(route_ctx.net_terminal_group_num,std::get<7>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.non_configurable_bitset,std::get<8>(routing_saved))),"restore non_configurable_bitset");\n            std::swap(route_ctx.non_configurable_bitset,std::get<8>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.net_status,std::get<9>(routing_saved))),"restore net_status");\n            std::swap(route_ctx.net_status,std::get<9>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.route_bb,std::get<10>(routing_saved))),"restore route_bb");\n            std::swap(route_ctx.route_bb,std::get<10>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.clb_opins_used_locally,std::get<11>(routing_saved))),"restore clb_opins_used_locally");\n            std::swap(route_ctx.clb_opins_used_locally,std::get<11>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.routing_id,std::get<12>(routing_saved))),"restore routing_id");\n            std::swap(route_ctx.routing_id,std::get<12>(routing_saved));\n            static_assert(noexcept(std::swap(route_ctx.is_flat,std::get<13>(routing_saved))),"restore is_flat");\n            std::swap(route_ctx.is_flat,std::get<13>(routing_saved));\n            if(placement_committed){registry.apply_move_blocks(reverse);registry.commit_move_blocks(reverse);}\n            setenv("ROUTECAST_NATIVE_SEED",original_seed.c_str(),1);setenv("ROUTECAST_TIMING_RESTORE_PROBE","1",1);\n            VTR_LOG("ROUTECAST restored routing and inverse committed placement before STA rebuild\\n");\n'+'            for(auto& entry:pb_saved)std::swap(*entry.first,entry.second);',1)
route=route.replace('bool route(', 'void print_route(const Netlist<>&,FILE*,bool);\n\nbool route(',1)
needle='            VTR_LOG("ROUTECAST actual moved candidate search completed before synchronization\\n");'
assert route.count(needle)==1
route=route.replace(needle,"""            FILE* candidate_file=std::fopen("candidate.route","w");
            if(!candidate_file)throw std::runtime_error("candidate trace capture failed");
            print_route(net_list,candidate_file,is_flat);std::fclose(candidate_file);
"""+needle,1)
route='#include "check_route.h"\n'+route
needle='            FILE* candidate_file=std::fopen("candidate.route","w");'
assert route.count(needle)==1
route=route.replace(needle,"""            check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
            VTR_LOG("ROUTECAST moved candidate passed native FULL routing check\\n");
"""+needle,1)
route='#include "globals.h"\n#include "read_place.h"\n'+route
needle='            vpr_throw(VPR_ERROR_ROUTE,__FILE__,__LINE__,"injected failure after candidate STA");'
assert route.count(needle)==1
route=route.replace(needle,"""            if(std::getenv("ROUTECAST_ACCEPT_CANDIDATE")) {
                check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
                g_vpr_ctx.mutable_placement().placement_id=print_place("design.net",mutable_cluster.clb_nlist.netlist_id().c_str(),"accepted.place",registry.block_locs());
                VTR_LOG("ROUTECAST accepted actual moved candidate after FULL check, packing sync and STA\\n");
                return true;
            }
"""+needle,1)
route=route.replace('bool route(', 'void routecast_arm_sync_ticket(const Netlist<>&,const DeviceContext&,const AtomContext&,const ClusteringContext&,const PlacementContext&);\n\nbool route(',1)
route=route.replace('                return true;','                routecast_arm_sync_ticket(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement());\n                return true;',1)
shutil.copyfile(root/'tools/native_candidate_sync_scoped/sync_once.cpp',src/'sync_once.cpp')
(src/'route.cpp').write_text(route)
objects=[]
for n in ('read_route','old_traceback','route','sync_once'):
 obj=out/(n+'.o');cmd=[*compilebase,'-I'+str(shared/'vpr/src/base'),'-c',str(src/(n+'.cpp')),'-o',str(obj)]
 with (out/(n+'.log')).open('w') as f:result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 if result.returncode:raise SystemExit(n+' failed')
 objects.append(str(obj))
archive=out/'libvpr.a';shutil.copyfile(shared/'build_tileplace_vpr/vpr/libvpr.a',archive);subprocess.run(['ar','d',str(archive),'read_route.cpp.o','old_traceback.cpp.o','route.cpp.o'],check=True)
link=protocol['link'];link=[str(archive) if p.endswith('/libvpr.a') else str(out/'routecast_search_seed_vpr') if p.endswith('/routecast_seed_vpr') else p for p in link];link=[p for p in link if not p.endswith('/hook.o') and not p.startswith('-Wl,--wrap=')];link[1:1]=objects+['-Wl,--wrap=_Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb']
with (out/'link.log').open('w') as f:res=subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,timeout=120)
assert all(sha(p)==h for p,h in original.items())
(out/'receipt.json').write_text(json.dumps({'exit_code':res.returncode,'shared_inputs_sha256':original,'sources_sha256':{str(p):sha(p) for p in src.iterdir()},'binary_sha256':sha(out/'routecast_search_seed_vpr') if res.returncode==0 else None,'scope':'Private read_route/traceback object replacement; explicit NET constructor and sink tables. Importer factors remain prototype constants.'},indent=2)+'\n');print(res.returncode)
