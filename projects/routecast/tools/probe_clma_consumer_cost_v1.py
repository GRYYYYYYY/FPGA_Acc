"""Structure-selected exposed CLMA baseline cost probe; no on/off acceleration claim."""
import json,hashlib,os,subprocess,time,resource,shutil,re,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'clma_consumer_cost_probe_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for x in iter(lambda:f.read(8<<20),b''):h.update(x)
 return h.hexdigest()
def main():
 D.mkdir(exist_ok=False);endpoint=E/'clma_frontend_validation_2026-10-04/endpoints.json';ep=json.loads(endpoint.read_text());net=Path(ep['inputs']['net']['path']);place=Path(ep['inputs']['place']['path']);graph=Path(ep['inputs']['graph']['path']);arch=V/'vtr_flow/arch/timing/k6_frac_N10_mem32K_40nm.xml';blif=V/'vtr_flow/benchmarks/blif/clma.blif';binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';build=binary.parent/'receipt.json';assert sha(binary)==json.loads(build.read_text())['binary_sha256'];packed=next(ET.iterparse(net,events=['start']))[1];assert packed.get('architecture_id')=='SHA256:'+sha(arch) and packed.get('atom_netlist_id')=='SHA256:'+sha(blif)
 for item in ep['inputs'].values():assert sha(item['path'])==item['sha256']
 width=None
 for ev,el in ET.iterparse(graph,events=['start']):
  if el.tag=='channel':width=int(el.get('chan_width_max'));assert {int(el.get(k)) for k in ['x_max','x_min','y_max','y_min']}=={width};break
 assert width==200 and graph.stat().st_size<=256<<20
 control=E/'freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';x=json.loads(control.read_text());koios=E/'koios_spmv_endpoints_v2_2026-10-04/endpoints.json';k=json.loads(koios.read_text());kgraph=Path(k['inputs']['graph']['path']);selection={'CLMA_connections':len(ep['connections']),'XTEA_connections':len(x['connections']),'CLMA_graph_bytes':graph.stat().st_size,'XTEA_graph_bytes':Path(x['inputs']['graph']['path']).stat().st_size,'Koios_graph_bytes':kgraph.stat().st_size,'XML_byte_screen_limit':256<<20,'Koios_status':'NOT_RUN_EXCEEDS_DECLARED_GRAPH_BYTE_SCREEN','selection_basis':'Original previously topology-validated CLMA/Koios fixtures, larger source-demand count than XTEA; resource byte screen. No route labels/quality/native time used for workload rank.'};assert selection['Koios_graph_bytes']>256<<20
 f=D/'native';f.mkdir();paths=[Path(__file__),endpoint,control,koios,net,place,graph,arch,blif,binary,build];protocol={'selection':selection,'scope':'Single exposed-development cold baseline cost probe, not model or paired placement experiment, strict unseen0. Existing frozen postpack CLMA graph/net/place, source input capture unpaid. No new source synthesis or semantic-policy variant.','budget':{'native_calls':1,'AS_GiB':8,'core_dump_bytes':0,'elapsed_timeout':None,'workers':1,'seed':1,'max_router_iterations':100,'width_from_frozen_graph':width},'economics':'No baseline alternative-candidate native calls invented. Baseline timing screens implementation plausibility only, not a rigorous upper bound on other placements or an acceleration result. Future on/off must count actual setup/model/decision/native/gates.','bindings':{str(p):sha(p) for p in paths}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');tick=time.perf_counter()
 for src,target in [(net,'clma.net'),(place,'clma.place'),(blif,'clma.blif')]:shutil.copyfile(src,f/target)
 cmd=[str(binary),str(arch),'clma.blif','--route','--net_file','clma.net','--place_file','clma.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width',str(width),'--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];(D/'command.json').write_text(json.dumps(cmd,indent=2)+'\n')
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 native_tick=time.perf_counter()
 with (f/'native.log').open('w') as log:code=subprocess.call(cmd,cwd=f,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
 text=(f/'native.log').read_text();result={'exit_code':code,'native_process_seconds':time.perf_counter()-native_tick,'copy_and_native_seconds':time.perf_counter()-tick,'child_peak_RSS_KiB':resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,'VPR_success':'VPR succeeded' in text,'full_native_self_check':'Completed routing consistency check successfully.' in text,'not_complete_gate':'Independent physical/endpoint/canonical/placement/model/timing gates not executed by this probe. No prediction or on/off decisions.'};(D/'result.json').write_text(json.dumps(result,indent=2)+'\n');assert all(sha(p)==h for p,h in protocol['bindings'].items());print('CLMA_COST_PROBE_TERMINAL',json.dumps(result),flush=True)
if __name__=='__main__':main()
