"""Private legal-seed incumbent and native CPD publication ceiling."""
import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'build/capacity_seed_incumbent_2026-10-06';out.mkdir();base=root/'build/native_search_seed_v3_2026-10-06';p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());s=(root/'build/capacity_prerelease_repair_2026-10-06/route.cpp').read_text();s='#include "check_route.h"\n'+s;needle='    const char* release_path=std::getenv("ROUTECAST_PRERELEASE_NET_NAMES");';assert s.count(needle)==1;s=s.replace(needle,'''    const bool seed_guard=std::getenv("ROUTECAST_SEED_INCUMBENT")!=nullptr;
    double seed_cpd_ceiling=0;
    if(seed_guard) {
        if(!routecast_seed||!*routecast_seed||is_flat||!router_opts.with_timing_analysis||router_opts.initial_timing!=e_router_initial_timing::LOOKAHEAD)throw std::runtime_error("seed incumbent requires timed cluster LOOKAHEAD seed");
        check_route(net_list,router_opts.route_type,e_check_route_option::FULL,is_flat);
        check_net_delays(net_list,net_delay);
        best_routing=route_ctx.route_trees;
        best_clb_opins_used_locally=route_ctx.clb_opins_used_locally;
        best_routing_metrics.sTNS=timing_info->setup_total_negative_slack();
        best_routing_metrics.sWNS=timing_info->setup_worst_negative_slack();
        best_routing_metrics.hTNS=timing_info->hold_total_negative_slack();
        best_routing_metrics.hWNS=timing_info->hold_worst_negative_slack();
        best_routing_metrics.critical_path=timing_info->least_slack_critical_path();
        best_routing_metrics.used_wirelength=calculate_wirelength_info(net_list,available_wirelength).used_wirelength();
        seed_cpd_ceiling=double(best_routing_metrics.critical_path.delay());
        success=true;
        VTR_LOG("ROUTECAST_SEED_INCUMBENT cpd_ns=%.9g\\n",seed_cpd_ceiling*1e9);
    }
'''+needle);needle='            if (is_better_quality_routing(best_routing, best_routing_metrics, wirelength_info, timing_info)) {';assert s.count(needle)==1;s=s.replace(needle,'''            if(seed_guard)VTR_LOG("ROUTECAST_INCUMBENT_CANDIDATE iter=%d cpd_ns=%.9g admissible=%d\\n",itry,double(critical_path.delay())*1e9,int(double(critical_path.delay())<=seed_cpd_ceiling));
            if ((!seed_guard || double(critical_path.delay())<=seed_cpd_ceiling) && is_better_quality_routing(best_routing, best_routing_metrics, wirelength_info, timing_info)) {''');(out/'route.cpp').write_text(s);obj=out/'route.o'
with (out/'compile.log').open('w') as f:subprocess.run([*p['compile'][:-4],'-c',str(out/'route.cpp'),'-o',str(obj)],stdout=f,stderr=subprocess.STDOUT,check=True)
archive=root/'build/capacity_dirty_repair_2026-10-06/libvpr.a';exe=out/'guard_vpr';link=[str(archive) if x.endswith('/libvpr.a') else str(exe) if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link[1:1]=[str(base/(n+'.o')) for n in ('read_route','old_traceback')]+[str(obj),str(root/'build/capacity_dirty_repair_2026-10-06/route_net.o')]
with (out/'link.log').open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True)
(out/'receipt.json').write_text(json.dumps({'binary_sha256':sha(exe),'source_sha256':sha(out/'route.cpp'),'inputs_sha256':{x:sha(x) for x in link if x.endswith(('.o','.a'))},'scope':'Native legal-seed best-routing incumbent with seed CPD ceiling. Timed cluster LOOKAHEAD only, fresh process prototype. Does not implement exception-safe transaction, packed bundle publishing or cold-quality guarantee.'},indent=2)+'\n');print('built')
