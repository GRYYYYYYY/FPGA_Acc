"""Versioned complete event audits; preserve v1 path-binding failures and predictions."""
import json,subprocess,sys,time,os
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_feedback_cohort_v1_2026-10-20'
def main():
 p=D/'protocol.json';v=json.loads(p.read_text());verifier=R/'tools/verify_prince_current_timing_feedback_events_v2.py';bindings={str(f):sha(f) for f in [p,Path(__file__),verifier,R/'tools/audit_prince_structural_node_base_v1.py']};rows=[]
 (D/'audit_protocol_v2.json').write_text(json.dumps(dict(bindings=bindings,policy='Only graph-content binding corrected: exact target graph SHA equals bound source graph SHA; all bound source files rehashed, full native price/XML/Fraction and event replay retained. Producer and v1 failures immutable. No model/prediction changes.'),indent=2)+'\n')
 for j in v['jobs']:
  out=Path(j['output']);receipt=out/'receipt.json';target=out/'complete_event_audit_v2.json'
  while not receipt.exists():
   if (D/'receipt.json').exists():break
   time.sleep(1)
  if not receipt.exists():rows.append(dict(case=j['case'],arm=j['arm'],passed=False,reason='producer_has_no_receipt'));continue
  if target.exists():
   d=json.loads(target.read_text());assert all(sha(f)==h for f,h in d['bindings'].items());code=0
  else:
   with (out.parent/(j['arm']+'_audit_v2.log')).open('x') as f:code=subprocess.call([sys.executable,str(verifier),str(out),j['case']+'_'+j['arm'],str(target)],stdout=f,stderr=subprocess.STDOUT,cwd=R)
  row=dict(case=j['case'],arm=j['arm'],exit_code=code,passed=code==0,verification=str(target));rows.append(row);(D/'audit_progress_v2.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n');print('AUDIT_V2',j['case'],j['arm'],code,flush=True)
 assert all(sha(f)==h for f,h in bindings.items());(D/'audit_receipt_v2.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,original_v1_failures_retained=True),indent=2)+'\n')
if __name__=='__main__':main()
