"""Import/audit three existing source paths, no route search or target labels."""
import concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_source_checkpoints_v1_2026-10-20';F=R/'experiments/wbuart_frame_raw_floors_v1_2026-10-20';E=R/'experiments/wbuart_width_frames_v2_2026-10-20';N=R/'experiments/wbuart_native_sources_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);origin=F/'independent_cache_origin_verification_v1.json';p=json.loads(origin.read_text());assert p['connections']==29916 and p['new_unique_queries']==7998
 for n,h in p['bindings'].items():assert sha(Path(n))==h
 producer=R/'tools/prepare_external_native_source_checkpoint_v1.py';auditor=R/'tools/verify_external_native_source_checkpoint_xml_v1.py';jobs=[];bindings={str(p):sha(p) for p in [Path(__file__),origin,producer,auditor]}
 for w in [96,128,160]:
  ep=E/f'w{w:03d}/source/routing_endpoints.json';route=N/f'native/w{w:03d}/source/output.route';floor=F/f'w{w:03d}/source/verification.json';nativeproof=N/f'native/w{w:03d}/source/verification.json';v=json.loads(nativeproof.read_text());assert v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS'
  for n,h in v['bindings'].items():assert sha(Path(n))==h
  parent=O/f'w{w:03d}';parent.mkdir();out=parent/'source';jobs.append({'width':w,'endpoint':str(ep),'route':str(route),'floor_proof':str(floor),'output':str(out)});bindings.update({str(p):sha(p) for p in [ep,route,floor,nativeproof]})
 (O/'protocol.json').write_text(json.dumps({'jobs':jobs,'bindings':bindings,'role':'Source checkpoint preparation only. Current per-width2493 routed CID universe, full CID provenance retained; paths from existing verified cold source, history empty, all epochs0. Original anchored proxy budget rule unchanged, no target route labels or native STA claim. Independent original XML/Fraction audit shares only printed-route parser with producer; native/canonical gates inherited separately. All prep/audit costs remain paid.'},indent=2)+'\n')
 def run(job):
  out=Path(job['output']);commands=[[sys.executable,str(producer),job['endpoint'],job['route'],job['floor_proof'],job['output']],[sys.executable,str(auditor),job['output']]]
  for label,cmd in zip(['producer','audit'],commands):
   with (out.parent/(label+'.log')).open('x') as log:rc=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
   if rc:print('CHECKPOINT_FAILURE',job['width'],label,rc,flush=True);return {'width':job['width'],'stage':label,'exit_status':rc}
  vp=out/'independent_xml_verification_v1.json';v=json.loads(vp.read_text());assert v['connections']==2493 and v['all_native_paths_exact'] and v['all_native_delays_and_budgets_exact'];print('WBUART_CHECKPOINT_VERIFIED',job['width'],v['connections'],flush=True);return {'width':job['width'],'exit_status':0,'verification':str(vp),'sha256':sha(vp),'connections':v['connections'],'nets':v['nets'],'anchored_above_proxy':v['anchored_above_proxy']}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,jobs))
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'terminal.json').write_text(json.dumps({'status':'ALL3_CHECKPOINT_WORKERS_TERMINAL','rows':rows,'all_pass':all(r['exit_status']==0 for r in rows),'bindings':{str(O/'protocol.json'):sha(O/'protocol.json')},'strict_unseen_admitted':False,'new_target_route_labels':False},indent=2)+'\n')
if __name__=='__main__':main()
