"""Private explicit API bridge; preserve shared VTR and existing private archive."""
import sys,json,shutil,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[2];old=R/'build/native_resume_singlepass_floor_2026-10-07';p=json.loads((old/'protocol.json').read_text());out=R/'build/native_route_transaction_post_route_v4_2026-10-07';out.mkdir();(out/'source').mkdir();hook=R/'tools/native_route_transaction/hook_post_route_v4.cpp';shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';api=shared/'vpr/src/base/vpr_api.cpp';s=api.read_text();needle='bool vpr_analysis_flow(const Netlist<>& net_list,';assert s.count(needle)==1;s=s.replace(needle,'bool routecast_original_analysis_flow(const Netlist<>& net_list,')
s+='\nextern bool routecast_after_routing(const Netlist<>&,t_vpr_setup&,const t_arch&,const RouteStatus&,bool);\nbool vpr_analysis_flow(const Netlist<>& n,t_vpr_setup& s,const t_arch& a,const RouteStatus& r,bool f){return routecast_after_routing(n,s,a,r,f);}\n'
privateapi=out/'source/vpr_api.cpp';privateapi.write_text(s);shutil.copyfile(hook,out/'source/hook.cpp');shutil.copyfile(__file__,out/'source/build.py');archive=out/'libvpr.a';exe=out/'routecast_transaction_vpr';obj=out/'vpr_api.cpp.o';hookobj=out/'hook.o';compile=p['compile'][:-4];assert p['compile'][-4]=='-c';commands=[compile+['-c',str(privateapi),'-o',str(obj)],compile+['-c',str(hook),'-o',str(hookobj)]]
link=[str(exe) if x==str(old/'routecast_resume_vpr') else str(archive) if x==str(old/'libvpr.a') else x for x in p['link']];link[1:1]=['-rdynamic',str(hookobj),'-Wl,--wrap=_Z10read_routePKcRK13t_router_optsbb','-Wl,--wrap=_Z24sync_netlists_to_routingRK7NetlistIN3vtr8StrongIdI18general_blk_id_tagiLin1EEENS1_I19general_port_id_tagiLin1EEENS1_I18general_pin_id_tagiLin1EEENS1_I18general_net_id_tagiLin1EEEERK13DeviceContextR11AtomContextR17ClusteringContextRK16PlacementContextRKb'];inputs={str(api):sha(api),str(old/'libvpr.a'):sha(old/'libvpr.a')};inputs.update({x:sha(x) for x in link if x.endswith(('.a','.o')) and x not in (str(archive),str(hookobj))});protocol=dict(inputs=inputs,hook_sha256=sha(hook),api_sha256=sha(privateapi),builder_sha256=sha(__file__),compile=commands,link=link);(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter()
for i,cmd in enumerate(commands):
 with (out/f'compile_{i}.log').open('w') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 if r.returncode:raise SystemExit(r.returncode)
shutil.copyfile(old/'libvpr.a',archive)
for cmd in (['ar','r',str(archive),str(obj)],['ranlib',str(archive)],link):
 with (out/'link.log').open('a') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=120)
 if r.returncode:raise SystemExit(r.returncode)
assert all(sha(p)==h for p,h in inputs.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),binary_sha256=sha(exe),private_archive_sha256=sha(archive),wall_s=time.perf_counter()-start),indent=2)+'\n');print(exe)
