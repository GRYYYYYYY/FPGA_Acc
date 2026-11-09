import json,subprocess,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'build/capacity_dirty_repair_2026-10-06';out=root/'build/capacity_search_entry_capture_2026-10-06';out.mkdir();p=json.loads((root/'build/native_seed_import_v2_2026-10-06/protocol.json').read_text());s=(base/'route_net.cpp').read_text();helper='''
static void routecast_entry_snapshot(const Netlist<>& nets,ParentNetId net,int iteration,const char* phase) {
 const char* dir=std::getenv("ROUTECAST_ENTRY_CAPTURE_DIR");
 if(!dir||nets.net_name(net)!="new_n761")return;
 const auto& device=g_vpr_ctx.device();const auto& routing=g_vpr_ctx.routing();
 std::string stem=std::string(dir)+"/iter_"+std::to_string(iteration)+"_"+phase;
 FILE* f=std::fopen((stem+".nodes.tsv").c_str(),"w");if(!f)throw std::runtime_error("entry snapshot open failed");
 std::fprintf(f,"node\\toccupancy\\tcapacity\\tacc_cost\\tbase_cost\\n");
 for(auto node:device.rr_graph.nodes())std::fprintf(f,"%zu\\t%d\\t%d\\t%.9g\\t%.9g\\n",size_t(node),routing.rr_node_route_inf[node].occ(),device.rr_graph.node_capacity(node),double(routing.rr_node_route_inf[node].acc_cost),double(get_single_rr_cong_base_cost(node)));
 if(std::fclose(f))throw std::runtime_error("entry snapshot close failed");
 f=std::fopen((stem+".members.tsv").c_str(),"w");if(!f)throw std::runtime_error("membership snapshot open failed");
 std::fprintf(f,"node\\tnet\\tname\\n");
 for(auto owner:nets.nets())if(routing.route_trees[owner])for(const auto& node:routing.route_trees[owner]->all_nodes())std::fprintf(f,"%zu\\t%zu\\t%s\\n",size_t(node.inode),size_t(owner),nets.net_name(owner).c_str());
 if(std::fclose(f))throw std::runtime_error("membership snapshot close failed");
}
''';i=s.index('void setup_net(');s=s[:i]+helper+s[i:];needle='    /* "tree" points to this net';assert s.count(needle)==1;s=s.replace(needle,'    routecast_entry_snapshot(net_list,net_id,itry,"before_setup");\n'+needle);needle='    // completed constructing the partial route tree and updated all other data structures to match';s=s.replace(needle,'    routecast_entry_snapshot(net_list,net_id,itry,"after_setup");\n'+needle);(out/'route_net.cpp').write_text(s);obj=out/'route_net.o'
with (out/'compile.log').open('w') as f:subprocess.run([*p['compile'][:-4],'-c',str(out/'route_net.cpp'),'-o',str(obj)],stdout=f,stderr=subprocess.STDOUT,check=True)
archive=out/'libvpr.a';shutil.copyfile(base/'libvpr.a',archive);variants={}
for arm in ('sequential','prerelease'):
 seed=root/'build/native_search_seed_v3_2026-10-06';route=seed/'route.o' if arm=='sequential' else root/'build/capacity_prerelease_repair_2026-10-06/route.o';exe=out/(arm+'_vpr');link=[str(archive) if x.endswith('/libvpr.a') else str(exe) if x.endswith('/routecast_seed_vpr') else x for x in p['link']];link=[x for x in link if not x.endswith('/hook.o') and not x.startswith('-Wl,--wrap=')];link[1:1]=[str(seed/(n+'.o')) for n in ('read_route','old_traceback')]+[str(route),str(obj)]
 with (out/(arm+'_link.log')).open('w') as f:subprocess.run(link,stdout=f,stderr=subprocess.STDOUT,check=True)
 variants[arm]={'binary_sha256':sha(exe),'inputs_sha256':{x:sha(x) for x in link if x.endswith(('.a','.o'))}}
(out/'receipt.json').write_text(json.dumps({'variants':variants,'source_sha256':sha(out/'route_net.cpp'),'scope':'Snapshot immediately before/after setup_net, before fanout base-cost adjustment and connection expansion. Not exact per-edge search-cost capture; serial one-task diagnostic.'},indent=2)+'\n');print('built')
