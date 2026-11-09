"""Exact native producer identity, all4 outcome reviews; no timeout/restart."""
import json,sys,time,subprocess,traceback,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
root=R/'experiments/prospective_native_width_stress_v1_2026-10-18'
def live(identity):
 p=Path('/proc',str(identity['pid']),'stat')
 try:s=p.read_text().split(') ',1)[1].split()
 except FileNotFoundError:return False
 return s[19]==identity['startticks'] and s[0]!='Z'
def save(status,**extra):(root/'review_supervision.json').write_text(json.dumps(dict(status=status,**extra),indent=2)+'\n')
def main():
 producer=json.loads((root/'live_process.json').read_text());spec=R/'experiments/prospective_native_width_stress_protocol_v1_2026-10-18/protocol.json';p=json.loads(spec.read_text());logs=root/'review_logs';logs.mkdir();s=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(root/'review_live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=s[19]))+'\n');rows=[];bindings={str(spec):sha(spec),str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
 for name in p['order']:
  terminal=root/name/'terminal.json';save('waiting_fixed_native_job_terminal',job=name,producer=producer,completed=len(rows))
  while True:
   if terminal.exists():
    try:json.loads(terminal.read_text());break
    except json.JSONDecodeError:
     if not live(producer):raise
   if not live(producer):raise RuntimeError('Native producer terminal/missing before required job outcome; no restart')
   time.sleep(3)
  proof=root/name/'independent_outcome_verification_v1.json';save('reviewing_native_job_outcome',job=name,completed=len(rows))
  if not proof.exists():
   with (logs/f'{name}.log').open('x') as f:code=subprocess.call([sys.executable,str(R/'tools/verify_native_width_stress_outcome_v1_2026_10_18.py'),name],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   if code!=0:rows.append(dict(name=name,review_pass=False,native_label_admitted=False,audit_exit_status=code));continue
  v=json.loads(proof.read_text());assert v['status']=='independent_native_outcome_inputs_and_full_RR_reference_review_pass' and all(sha(k)==h for k,h in v['bindings'].items());bindings[str(proof)]=sha(proof);rows.append(dict(name=name,design=v['design'],width=v['width'],review_pass=True,outcome=v['outcome'],reason=v['reason'],iterations_completed=v['iterations_completed'],proof=str(proof),successful_route_physical_canonical_admission=v['independent_route_path_capacity_canonical_admission']));print('WIDTH_JOB_INDEPENDENT_REVIEW',name,v['outcome'],v['reason'],flush=True)
 failures=[x for x in rows if x.get('outcome')=='OBSERVED_NATIVE_ROUTING_FAILURE_UNDER_FIXED100ITER_BUDGET'];success=[x for x in rows if x.get('outcome')=='NATIVE_SUCCESS_PENDING_INDEPENDENT_PHYSICAL_CANONICAL'];result=dict(status='all4_fixed_native_outcomes_reviewed_further_route_admission_pending',bindings=bindings,cases=rows,all4_native_outcome_reviews_pass=len(rows)==4 and all(x['review_pass'] for x in rows),observed_native_failures=len(failures),observed_native_successes_pending_external_route_admission=len(success),failure_reasons=sorted({x['reason'] for x in failures}),strict_unseen_families=0,scope='Only fixed observed native outcomes and streamed RR/input review. No intrinsic-unroutability proof, forecast classification result, successful physical/canonical route admission, heldout or accepted matched-flow gain.');(root/'independent_outcome_cohort_v1.json').write_text(json.dumps(result,indent=2)+'\n');save('all4_native_outcomes_reviewed',all_reviews_pass=result['all4_native_outcome_reviews_pass'])
if __name__=='__main__':
 try:main()
 except Exception:save('review_pipeline_failed',error=traceback.format_exc());raise
