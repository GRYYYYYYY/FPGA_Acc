import json,subprocess,shutil
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
root=Path.cwd();base=root/'build/native_candidate_move_accept_scoped_2026-10-06';out=root/'build/native_candidate_retained_split_cost_2026-10-06';out.mkdir();src=out/'source';src.mkdir();p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());shared={f:sha(f) for f in p['inputs_sha256']}
s=(base/'source/route.cpp').read_text();start='    if (std::getenv("ROUTECAST_TIMING_RESTORE_PROBE")) {'
s=s.replace(start,start+'''\n        const char* raw_sequence=std::getenv("ROUTECAST_MOVE_SEQUENCE");
        std::string sequence=raw_sequence?raw_sequence:"A";
        if(sequence.empty() || sequence.find_first_not_of("AR")!=std::string::npos)throw std::runtime_error("invalid move sequence");
        for(size_t step=0;step<sequence.size();++step) {
        VTR_LOG("ROUTECAST sequence step=%zu decision=%c\\n",step,sequence[step]);
''',1)
s=s.replace('std::string original_seed=std::getenv("ROUTECAST_NATIVE_SEED");','const char* saved_seed_env=std::getenv("ROUTECAST_NATIVE_SEED");\n        std::string original_seed=saved_seed_env?saved_seed_env:"";')
s=s.replace('if(std::getenv("ROUTECAST_ACCEPT_CANDIDATE")) {',"if(sequence[step]=='A') {")
s=s.replace('                return true;','''                if(step+1==sequence.size())return true;
                sync_netlists_to_routing(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement(),quiet);
                continue;''',1)
s=s.replace('FILE* candidate_file=std::fopen("candidate.route","w");','std::string candidate_name="candidate_"+std::to_string(step)+".route";\n            FILE* candidate_file=std::fopen(candidate_name.c_str(),"w");')
needle='        VTR_LOG("ROUTECAST restored delay matrix and all edge-delay/STA metric observations\\n");\n    }'
assert s.count(needle)==1
s=s.replace(needle,'''        VTR_LOG("ROUTECAST restored delay matrix and all edge-delay/STA metric observations\\n");
        if(step+1==sequence.size()) {
            routecast_arm_sync_ticket(net_list,device_ctx,mutable_atom,mutable_cluster,g_vpr_ctx.placement());
            return true;
        }
        }
    }''')
s=s.replace('        for(size_t step=0;step<sequence.size();++step) {',r'''        // Canonical packing remains aligned with the immutable clustered pin namespace.
        std::vector<std::pair<t_pb*,t_pb>> canonical_pb;
        auto canonical_collect=[&](auto&& self,t_pb* pb)->void {
            canonical_pb.emplace_back(pb,*pb);
            if(pb->child_pbs)for(int t=0;t<pb->get_num_child_types();++t)for(int c=0;c<pb->get_num_children_of_type(t);++c)self(self,&pb->child_pbs[t][c]);
        };
        auto& canonical_cluster=g_vpr_ctx.mutable_clustering();
        for(auto block:canonical_cluster.clb_nlist.blocks())canonical_collect(canonical_collect,canonical_cluster.clb_nlist.block_pb(block));
        const auto canonical_lookup=g_vpr_ctx.atom().lookup;
        const auto canonical_post=canonical_cluster.post_routing_clb_pin_nets;
        const auto canonical_pre=canonical_cluster.pre_routing_net_pin_mapping;
        for(size_t step=0;step<sequence.size();++step) {''',1)
s=s.replace('            unsetenv("ROUTECAST_NATIVE_SEED");',r'''            for(const auto& entry:canonical_pb)*entry.first=entry.second;
            mutable_atom.lookup=canonical_lookup;
            mutable_cluster.post_routing_clb_pin_nets=canonical_post;
            mutable_cluster.pre_routing_net_pin_mapping=canonical_pre;
            delay_calc->clear_cache();
            for(auto edge:g_vpr_ctx.timing().graph->edges())timing_info->invalidate_delay(edge);
            VTR_LOG("ROUTECAST candidate uses canonical packing view at step=%zu\n",step);
            unsetenv("ROUTECAST_NATIVE_SEED");''',1)
s='#include <sstream>\n'+s
s=s.replace('        auto& registry=g_vpr_ctx.mutable_placement().mutable_blk_loc_registry();',r'''        const char* pair_env=std::getenv("ROUTECAST_MOVE_PAIRS");
        if(!pair_env)throw std::runtime_error("missing explicit move pairs");
        std::istringstream pair_stream(pair_env);int a=-1,b=-1;
        for(size_t i=0;i<=step;++i)if(!(pair_stream>>a>>b))throw std::runtime_error("missing move pair for step");
        if(a<0 || b<0 || a==b || size_t(a)>=mutable_cluster.clb_nlist.blocks().size() || size_t(b)>=mutable_cluster.clb_nlist.blocks().size())throw std::runtime_error("invalid move pair");
        ClusterBlockId pair_a(a),pair_b(b);
        VTR_LOG("ROUTECAST selected move pair step=%zu blocks=%d,%d\n",step,a,b);
        auto& registry=g_vpr_ctx.mutable_placement().mutable_blk_loc_registry();''',1)
s=s.replace('ClusterBlockId(0)','pair_a').replace('ClusterBlockId(1)','pair_b')
s=s.replace('        for(size_t step=0;step<sequence.size();++step) {',r'''        bool baseline_quiet=false;
        sync_netlists_to_routing(net_list,device_ctx,g_vpr_ctx.mutable_atom(),canonical_cluster,g_vpr_ctx.placement(),baseline_quiet);
        delay_calc->clear_cache();
        for(auto edge:g_vpr_ctx.timing().graph->edges())timing_info->invalidate_delay(edge);
        timing_info->update();
        auto& baseline_registry=g_vpr_ctx.mutable_placement().mutable_blk_loc_registry();
        g_vpr_ctx.mutable_placement().placement_id=print_place("design.net",canonical_cluster.clb_nlist.netlist_id().c_str(),"accepted.place",baseline_registry.block_locs());
        VTR_LOG("ROUTECAST synchronized baseline CPD=%g ns\n",1.e9*timing_info->least_slack_critical_path().delay());
        for(size_t step=0;step<sequence.size();++step) {''',1)
s=s.replace("if(sequence[step]=='A') {", "if(sequence[step]=='A' && std::get<0>(metrics())<=std::get<0>(before)) {")
s=s.replace('void print_route(const Netlist<>&,FILE*,bool);',r'''thread_local decltype(g_vpr_ctx.mutable_routing().route_trees) routecast_retained;
thread_local bool routecast_retained_pending=false;
void print_route(const Netlist<>&,FILE*,bool);''',1)
s=s.replace('    const char* routecast_seed =', '    const bool retained_input=routecast_retained_pending;\n    const char* routecast_seed =',1)
marker='    IntraLbPbPinLookup intra_lb_pb_pin_lookup'
s=s.replace(marker,r'''    if(retained_input) {
        routecast_retained_pending=false;
        size_t retained_nets=0;
        for(auto net:net_list.nets()) {
            if(!routecast_retained[net])continue;
            const auto& tree=routecast_retained[net].value();
            if(tree.root().inode!=route_ctx.net_rr_terminals[net][0])throw std::runtime_error("retained SOURCE changed");
            for(size_t pin=1;pin<net_list.net_pins(net).size();++pin){auto sink=tree.find_by_isink(pin);if(!sink || sink->inode!=route_ctx.net_rr_terminals[net][pin])throw std::runtime_error("retained SINK changed");}
            route_ctx.route_trees[net]=std::move(routecast_retained[net]);
            route_ctx.route_trees[net]->reload_timing();++retained_nets;
        }
        routecast_retained.clear();
        FourAryHeap retained_heap;retained_heap.init_heap(device_ctx.grid);
        reserve_locally_used_opins(&retained_heap,router_opts.initial_pres_fac,router_opts.acc_fac,false,is_flat);
        recompute_occupancy_from_scratch(net_list,is_flat);
        OveruseInfo retained_overuse(device_ctx.rr_graph.num_nodes());
        pathfinder_update_acc_cost_and_overuse_info(router_opts.acc_fac,retained_overuse);
        reserve_locally_used_opins(&retained_heap,router_opts.initial_pres_fac,router_opts.acc_fac,true,is_flat);
        recompute_occupancy_from_scratch(net_list,is_flat);
        VTR_LOG("ROUTECAST validated retained NET trees=%zu in candidate initialization\n",retained_nets);
    }
'''+marker,1)
s=s.replace('if (routecast_seed && *routecast_seed && router_opts.initial_timing', 'if ((retained_input || (routecast_seed && *routecast_seed)) && router_opts.initial_timing')
s=s.replace('        if (routecast_seed && *routecast_seed) {', '        if (retained_input || (routecast_seed && *routecast_seed)) {')
s=s.replace('            bool candidate_ok=route(',r'''            routecast_retained.clear();routecast_retained.resize(std::get<0>(routing_saved).size());
            for(auto net:net_list.nets()) {
                if(net_list.net_is_ignored(net) || !std::get<0>(routing_saved)[net])continue;
                bool dirty=false;
                for(auto pin:net_list.net_pins(net)){auto block=net_list.pin_block(pin);if(size_t(block)==size_t(pair_a) || size_t(block)==size_t(pair_b))dirty=true;}
                if(!dirty)routecast_retained[net]=std::get<0>(routing_saved)[net];
            }
            routecast_retained_pending=true;
            bool candidate_ok=route(''',1)
s=s.replace('        } catch(const VprError&) {', '        } catch(const VprError&) {\n            routecast_retained_pending=false;routecast_retained.clear();',1)
s='#include <chrono>\n'+s
s=s.replace('        auto refresh=[&]() {',r'''        using RCClock=std::chrono::steady_clock;
        auto phase_begin=RCClock::now();
        auto phase=[&](const char* name){auto end=RCClock::now();VTR_LOG("ROUTECAST phase step=%zu name=%s us=%lld\n",step,name,(long long)std::chrono::duration_cast<std::chrono::microseconds>(end-phase_begin).count());phase_begin=end;};
        auto refresh=[&]() {''',1)
s=s.replace('        try {', '        phase("snapshot");\n        try {',1)
s=s.replace('            unsetenv("ROUTECAST_NATIVE_SEED");', '            phase("placement_and_canonical_view");\n            unsetenv("ROUTECAST_NATIVE_SEED");',1)
s=s.replace('            if(!candidate_ok)', '            phase("native_search");\n            if(!candidate_ok)',1)
s=s.replace('            bool quiet=false;', '            phase("candidate_full_check_and_capture");\n            bool quiet=false;',1)
s=s.replace('            refresh();mutation=(metrics()!=before);', '            refresh();phase("packing_sync_and_STA");mutation=(metrics()!=before);',1)
s=s.replace('                return true;', '                return true;',1)
s=s.replace('        } catch(const VprError&) {','        } catch(const VprError&) {\n            phase_begin=RCClock::now();',1)
s=s.replace('        if(!rejected || !mutation', '        phase("restore_and_STA");\n        if(!rejected || !mutation',1)
s=s.replace('            routecast_retained.clear();routecast_retained.resize', '            auto rc_copy_start=std::chrono::steady_clock::now();\n            routecast_retained.clear();routecast_retained.resize',1)
s=s.replace('            routecast_retained_pending=true;', '            VTR_LOG("ROUTECAST retained copy step=%zu us=%lld\\n",step,(long long)std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-rc_copy_start).count());\n            routecast_retained_pending=true;',1)
s=s.replace('    if(retained_input) {', '    if(retained_input) {\n        auto rc_init_start=std::chrono::steady_clock::now();',1)
s=s.replace('        VTR_LOG("ROUTECAST validated retained NET trees=', '        VTR_LOG("ROUTECAST retained import us=%lld\\n",(long long)std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-rc_init_start).count());\n        VTR_LOG("ROUTECAST validated retained NET trees=',1)
(src/'route.cpp').write_text(s);shutil.copyfile(base/'source/sync_once.cpp',src/'sync_once.cpp');shutil.copyfile(__file__,src/'build.py')
obj=out/'route.o';cmd=[*p['compile'][:-4],'-c',str(src/'route.cpp'),'-o',str(obj)]
with (out/'compile.log').open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
link=[str(base/'libvpr.a') if x.endswith('/libvpr.a') else str(out/'sequence_vpr') if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')]
import re
wrap=re.search(r"'-Wl,--wrap=_Z24[^']+'",(root/'tools/native_search_seed/build_candidate_move_accept_scoped.py').read_text())[0][1:-1]
link[1:1]=[str(base/'read_route.o'),str(base/'old_traceback.o'),str(obj),str(base/'sync_once.o'),wrap]
with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
assert all(sha(f)==h for f,h in shared.items())
(out/'receipt.json').write_text(json.dumps({'shared_inputs_sha256':shared,'binary_sha256':sha(out/'sequence_vpr'),'source_sha256':{str(f):sha(f) for f in src.iterdir()},'scope':'Serial same-process recursive cold-candidate sequence, fixed compatible block pair. Not a production transaction.'},indent=2)+'\n');print('built')
