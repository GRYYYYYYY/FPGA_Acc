"""Frozen all-nine development initializer availability; no target route label inputs."""
import json,subprocess,sys,time,resource
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_warm_initializers_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
def main():
 D.mkdir(exist_ok=False);jobs=[];bindings={str(Path(__file__)):sha(__file__)}
 producer=R/'tools/prepare_external_warm_initializers_v1.py';verifier=R/'tools/verify_external_warm_initializers_xml_v1.py'
 for f in [producer,verifier]:bindings[str(f)]=sha(f)
 for width in [96,128,160]:
  for episode in [1,2,3]:
   case=f'w{width:03d}/episode_{episode:02d}';ep=E/'prince_native_cohort_v1_2026-10-20'/case/'pre_route_endpoints.json';fp=E/'prince_frame_raw_floors_v1_2026-10-20'/case/'verification.json';src=E/'prince_native_source_checkpoints_v1_2026-10-20'/f'w{width:03d}';available=(src/'independent_xml_verification_v1.json').exists()
   paths=[ep,fp]+([src/'independent_xml_verification_v1.json',src/'initial.json'] if available else [])
   for f in paths:bindings[str(f)]=sha(f)
   jobs.append(dict(case=case,available_source=available,endpoint=str(ep),source=str(src),floor_proof=str(fp),output=str(D/case)))
 (D/'protocol.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,policy='All9 targets retained; source96 missing => unavailable, never substitute failed route. Existing exact raw_min/native_retained initializer algorithms and independent XML/Fraction audits unchanged. No target occupancy/route or metric labels passed to either initializer. Timings component-only, serial fixed order.'),indent=2)+'\n');results=[];start=time.perf_counter()
 for j in jobs:
  if not j['available_source']:results.append(dict(case=j['case'],status='UNAVAILABLE_LEGAL_SOURCE'));continue
  out=Path(j['output']);out.parent.mkdir(parents=True,exist_ok=True);log=out.parent/(out.name+'_producer.log');tick=time.perf_counter()
  with log.open('x') as f:code=subprocess.call([sys.executable,str(producer),j['endpoint'],j['source'],j['floor_proof'],j['output']],stdout=f,stderr=subprocess.STDOUT,cwd=R,preexec_fn=limit)
  audits=[]
  if code==0:
   for arm in ['raw_min','native_retained']:
    with (out/(arm+'_audit.log')).open('x') as f:rc=subprocess.call([sys.executable,str(verifier),str(out/arm)],stdout=f,stderr=subprocess.STDOUT,cwd=R,preexec_fn=limit)
    audits.append(dict(arm=arm,exit_code=rc,verification=str(out/arm/'verification.json')))
  row=dict(case=j['case'],producer_exit_code=code,audits=audits,status='BOTH_INITIALIZERS_XML_VERIFIED' if code==0 and len(audits)==2 and all(x['exit_code']==0 for x in audits) else 'FAILURE_RETAINED',seconds=time.perf_counter()-tick);results.append(row);(D/'progress.json').write_text(json.dumps(dict(results=results),indent=2)+'\n');print('PRINCE_WARM',j['case'],row['status'],flush=True)
 assert all(sha(f)==h for f,h in bindings.items())
 (D/'receipt.json').write_text(json.dumps(dict(results=results,bindings=bindings,continuous_seconds=time.perf_counter()-start,strict_unseen_admitted=False,scope='Initializer path/budget/ledger validity only, no prediction quality, legal route acceptance or matched full-flow gain.'),indent=2)+'\n')
if __name__=='__main__':main()
