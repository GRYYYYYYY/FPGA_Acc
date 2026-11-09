import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';out=root/'build/capacity_connection_capture_2026-10-06';out.mkdir(exist_ok=True);src=out/'source';src.mkdir(exist_ok=True);p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text())
for pattern in ('*.h','*.tpp'):
 for f in (shared/'vpr/src/route').glob(pattern):
  if 'netlist' in f.name.lower() or f.name in ('route_net.h','route_net.tpp'):shutil.copyfile(f,src/f.name)
  elif (src/f.name).exists():(src/f.name).unlink()
f=src/'route_net.tpp';s=f.read_text();helper='''
inline void routecast_connection_capture(const Netlist<>& nets,ParentNetId net,int iteration,unsigned order,int pin,float crit,float pres,const t_conn_cost_params& cost,const RouteTree& tree,const char* phase){
 const char* dir=std::getenv("ROUTECAST_CONNECTION_CAPTURE_DIR");if(!dir||nets.net_name(net)!="new_n761")return;
 const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();
 std::string stem=std::string(dir)+"/iter_"+std::to_string(iteration)+"_order_"+std::to_string(order)+"_pin_"+std::to_string(pin)+"_"+phase;
 FILE* f=std::fopen((stem+".tsv").c_str(),"w");if(!f)throw std::runtime_error("connection snapshot open failed");
 std::fprintf(f,"iteration\\torder\\tpin\\tcriticality\\tpres_fac\\tastar_fac\\n%d\\t%u\\t%d\\t%.9g\\t%.9g\\t%.9g\\n",iteration,order,pin,double(crit),double(pres),double(cost.astar_fac));
 std::fprintf(f,"node\\toccupancy\\tcapacity\\tacc_cost\\tbase_cost\\tcong_cost\\n");
 for(auto n:device.rr_graph.nodes())std::fprintf(f,"%zu\\t%d\\t%d\\t%.9g\\t%.9g\\t%.9g\\n",size_t(n),routing.rr_node_route_inf[n].occ(),device.rr_graph.node_capacity(n),double(routing.rr_node_route_inf[n].acc_cost),double(get_single_rr_cong_base_cost(n)),double(get_rr_cong_cost(n,pres)));
 if(std::fclose(f))throw std::runtime_error("connection snapshot close failed");
 f=std::fopen((stem+".tree.tsv").c_str(),"w");if(!f)throw std::runtime_error("tree snapshot open failed");
 std::fprintf(f,"node\\tpin\\tdelay_s\\n");for(const auto& n:tree.all_nodes())std::fprintf(f,"%zu\\t%d\\t%.9g\\n",size_t(n.inode),n.net_pin_index,double(n.Tdel));
 if(std::fclose(f))throw std::runtime_error("tree snapshot close failed");
}
''';s='#include <cstdlib>\n#include <cstdio>\n#include <stdexcept>\n'+s;marker='template<typename ConnectionRouter>';idx=s.index(marker);s=s[:idx]+helper+s[idx:];needle='        // build a branch in the route tree to the target';assert s.count(needle)==1;s=s.replace(needle,'        routecast_connection_capture(net_list,net_id,itry,itarget,target_pin,pin_criticality[target_pin],pres_fac,cost_params,tree,"before");\n'+needle);needle='        profiling::conn_finish(';assert s.count(needle)==1;s=s.replace(needle,'        routecast_connection_capture(net_list,net_id,itry,itarget,target_pin,pin_criticality[target_pin],pres_fac,cost_params,tree,"after");\n'+needle);f.write_text(s);variants={}
for variant,source in [('sequential',root/'build/native_search_seed_v3_2026-10-06/source/route.cpp'),('prerelease',root/'build/capacity_prerelease_repair_2026-10-06/route.cpp')]:
 cpp=src/(variant+'.cpp');shutil.copyfile(source,cpp);obj=out/(variant+'.o')
 with (out/(variant+'_compile.log')).open('w') as log:subprocess.run([*p['compile'][:-4],'-c',str(cpp),'-o',str(obj)],stdout=log,stderr=subprocess.STDOUT,check=True)
 archive=root/'build/capacity_search_entry_capture_2026-10-06/libvpr.a';exe=out/(variant+'_vpr');base=root/'build/native_search_seed_v3_2026-10-06';link=[str(archive) if x.endswith('/libvpr.a') else str(exe) if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link[1:1]=[str(base/(n+'.o')) for n in ('read_route','old_traceback')]+[str(obj),str(root/'build/capacity_search_entry_capture_2026-10-06/route_net.o')]
 with (out/(variant+'_link.log')).open('w') as log:subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,check=True)
 variants[variant]={'binary_sha256':sha(exe),'inputs_sha256':{x:sha(x) for x in link if x.endswith(('.a','.o'))}}
(out/'receipt.json').write_text(json.dumps({'variants':variants,'source_sha256':{str(f):sha(f) for f in src.iterdir()},'scope':'Native connection entry/exit snapshots after fanout cost adjustment: target order, criticality, pres/astar factor, full live occupancy and native congestion cost, tree prefix. Serial diagnostic, no transaction or speed claim.'},indent=2)+'\n');print('built')
