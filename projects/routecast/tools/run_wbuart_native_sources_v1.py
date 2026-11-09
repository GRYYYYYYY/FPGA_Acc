"""Fixed three-width source conditioning, no target-label execution."""
import concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_native_sources_v1_2026-10-20';F=R/'experiments/wbuart_width_frames_v2_2026-10-20';S=R/'experiments/wbuart_development_place_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);ip=F/'independent_verification_v1.json';proof=json.loads(ip.read_text());assert len(proof['rows'])==12
 for n,h in proof['bindings'].items():assert sha(Path(n))==h
 build=R/'build/native_external_shared_sink_native_v1_2026-10-19/receipt.json';b=json.loads(build.read_text());binary=Path(b['binary']);assert sha(binary)==b['binary_sha256']
 for n,h in b['bindings'].items():assert sha(Path(n))==h
 template=R/'experiments/prospective_external_family_corrected_native_epoch_v1_2026-10-19/source_manifest.json';cmd0=json.loads(template.read_text())['cases'][0]['command'];assert cmd0[0]==str(binary);runner=R/'tools/run_wbuart_native_source_case_v1.py';bindings={str(p):sha(p) for p in [Path(__file__),runner,ip,build,binary,template,S/'design.blif',S/'design.net',S/'source.place',Path(cmd0[1])]};cases=[]
 for w in [96,128,160]:
  folder=F/f'w{w:03d}/source';ep=folder/'routing_endpoints.json';e=json.loads(ep.read_text());assert len(e['connections'])==2493;graph=folder/'rr_graph.xml';assert sha(graph)==e['graph_sha256'];cmd=cmd0.copy();cmd[cmd.index('--read_rr_graph')+1]=str(graph);cmd[cmd.index('--route_chan_width')+1]=str(w);assert cmd[cmd.index('--max_router_iterations')+1]=='300';bindings.update({str(p):sha(p) for p in [ep,graph,folder/'verification.json',folder/'native_ignored_partition.json']});cases.append({'case':f'w{w:03d}/source','width':w,'frame':'source','role':'development_source_conditioning_only','endpoint':str(ep),'graph_sha256':sha(graph),'inputs':{k:str(S/v) for k,v in [('blif','design.blif'),('net','design.net'),('place','source.place')]},'output':str(D/'native'/f'w{w:03d}/source'),'command':cmd})
 manifest={'schema':'ROUTECAST_WBUART_NATIVE_SOURCE_PREPARATION_V1','native_source_preparation_admitted':True,'complete_prediction_utility_workflow_admitted':False,'strict_unseen_admitted':False,'bindings':bindings,'cases':cases,'policy':'All three frozen widths, fixed300 iterations, seed1 worker1 corrected native. Retain every source failure; no extra widths/seeds/budget increases/restarts. Only source-conditioning paths; no target routes or predictor quality selection. Full physical/canonical audit mandatory. Costs are upstream paid dependencies, not net-gain evidence.'};mp=D/'manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');print('WBUART_SOURCE_MANIFEST_FROZEN',flush=True)
 def run(c):
  with (D/(c['case'].replace('/','_')+'.log')).open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  vp=Path(c['output'])/'verification.json';v=json.loads(vp.read_text()) if vp.exists() else {};row={'case':c['case'],'wrapper_exit_status':rc,'status':v.get('status','MISSING_VERIFICATION'),'error':v.get('error'),'verification':str(vp),'iterations':v.get('iterations')};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,cases))
 (D/'terminal.json').write_text(json.dumps({'status':'ALL3_FIXED_NATIVE_SOURCE_WORKERS_TERMINAL','rows':rows,'new_target_routes':False,'complete_prediction_utility_workflow_admitted':False,'strict_unseen_admitted':False},indent=2)+'\n')
if __name__=='__main__':main()
