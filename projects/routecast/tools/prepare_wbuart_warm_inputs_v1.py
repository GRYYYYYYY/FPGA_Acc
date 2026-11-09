"""Nine fixed swap inputs, both original initializer policies, no target labels."""
import concurrent.futures,hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/wbuart_warm_inputs_v1_2026-10-20';E=R/'experiments/wbuart_width_frames_v2_2026-10-20';F=R/'experiments/wbuart_frame_raw_floors_v1_2026-10-20';S=R/'experiments/wbuart_source_checkpoints_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);source_terminal=S/'terminal.json';st=json.loads(source_terminal.read_text());assert st['all_pass'] and len(st['rows'])==3
 producer=R/'tools/prepare_external_warm_initializers_v1.py';auditor=R/'tools/verify_external_warm_initializers_xml_v1.py';jobs=[];bindings={str(p):sha(p) for p in [Path(__file__),source_terminal,producer,auditor,F/'independent_cache_origin_verification_v1.json']}
 for w in [96,128,160]:
  sd=S/f'w{w:03d}/source';proof=json.loads((sd/'independent_xml_verification_v1.json').read_text());assert proof['connections']==2493
  for n,h in proof['bindings'].items():assert sha(Path(n))==h
  for i in [1,2,3]:
   case=f'w{w:03d}/episode_{i:02d}';ep=E/case/'routing_endpoints.json';floor=F/case/'verification.json';out=O/case;out.parent.mkdir(exist_ok=True);jobs.append({'case':case,'endpoint':str(ep),'source':str(sd),'floor':str(floor),'output':str(out)});bindings.update({str(p):sha(p) for p in [ep,floor,sd/'independent_xml_verification_v1.json']})
 (O/'protocol.json').write_text(json.dumps({'jobs':jobs,'bindings':bindings,'initializer_policies':['raw_min','native_retained'],'budget_policy':'NATIVE_ENDPOINT_ANCHORED_PROXY_V2 unchanged: same graph/pair max(proxy,source delay), changed pair proxy=max(ceil(scale*1ns),ceil(3*current floor/2)).','role':'Input-only preparation before target labels, fixed9 episodes×2 initializers. Every2493 CID and full_connection_id retained, same per-width source checkpoint and own current floors. Independent XML/Fraction budget/parent/ledger/epoch audits required. Overuse allowed forecast demand, not native legal routing or model acceptance. No source timing copied into targets.'},indent=2)+'\n')
 def run(job):
  out=Path(job['output']);cmd=[sys.executable,str(producer),job['endpoint'],job['source'],job['floor'],job['output']]
  with (out.parent/(out.name+'_producer.log')).open('x') as f:rc=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
  if rc:return {'case':job['case'],'stage':'producer','exit_status':rc}
  rows=[]
  for mode in ['raw_min','native_retained']:
   d=out/mode
   with (out.parent/(out.name+'_'+mode+'_audit.log')).open('x') as f:rc=subprocess.call([sys.executable,str(auditor),str(d)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   if rc:return {'case':job['case'],'stage':mode+'_audit','exit_status':rc}
   vp=d/'verification.json';v=json.loads(vp.read_text());rows.append({'mode':mode,'verification':str(vp),'sha256':sha(vp)})
  print('WBUART_WARM_INPUTS_VERIFIED',job['case'],flush=True);return {'case':job['case'],'exit_status':0,'arms':rows}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(run,jobs))
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'terminal.json').write_text(json.dumps({'status':'ALL9_WARM_INPUT_WORKERS_TERMINAL','all_pass':all(r['exit_status']==0 for r in rows),'rows':rows,'bindings':{str(O/'protocol.json'):sha(O/'protocol.json')},'new_native_target_route_labels':False,'strict_unseen_admitted':False},indent=2)+'\n')
 print('WARM_INPUT_TERMINAL',all(r['exit_status']==0 for r in rows),flush=True)
if __name__=='__main__':main()
