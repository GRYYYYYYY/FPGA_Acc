"""One audit owner; preserve original producer, no restarts, exact PID identity."""
import pathlib,json,sys,subprocess,time,concurrent.futures,os
R=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_soft_budget_all_NET_v1_2026-10-18';out=root/'independent_audits';out.mkdir();cp=json.loads((R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/supervision_checkpoint.json').read_text())['mmc_soft_budget_all_NET_v1'];pid,ticks=cp['pid'],cp['startticks'];submitted=set();rows=[];pending={};bindings=closure([pathlib.Path(__file__)]);s=pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split();(out/'live_process.json').write_text(json.dumps({'pid':os.getpid(),'startticks':s[19]})+'\n')
 def task(case,kind):
  script=R/f'tools/verify_soft_budget_feedback_{kind}_v1_2026_10_18.py';target=out/f'{case}_{kind}.json';arg='sketch' if kind=='frame' else 'mmc'
  with (out/f'{case}_{kind}.log').open('x') as log:code=subprocess.call([sys.executable,str(script),str(root/case),arg,str(target)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
  return dict(case=case,kind=kind,exit_status=code,verification=str(target))
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  while len(rows)<6:
   for case in ['case_01','case_02','case_03']:
    if (root/case/'receipt.json').exists() and case not in submitted:
     receipt=json.loads((root/case/'receipt.json').read_text());assert len(receipt['rounds'])==2 and all(len(x['events'])==55300 for x in receipt['rounds']);submitted.add(case)
     for kind in ['frame','events']:pending[pool.submit(task,case,kind)]=(case,kind)
     print('SOFT_AUDIT_SUBMITTED',case,flush=True)
   for future in list(pending):
    if future.done():
     row=future.result();rows.append(row);del pending[future];print('SOFT_AUDIT_DONE',row['case'],row['kind'],row['exit_status'],flush=True)
   (out/'stages.json').write_text(json.dumps({'submitted_cases':sorted(submitted),'finished':rows,'pending':list(pending.values())},indent=2)+'\n')
   if len(submitted)<3:
    try:st=pathlib.Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split();live=st[19]==ticks and st[0]!='Z'
    except FileNotFoundError:live=False
    if not live:
     # Recheck receipts once on the next iteration before classifying missing work.
     if all((root/c/'receipt.json').exists() for c in ['case_01','case_02','case_03']):continue
     raise RuntimeError('Producer stopped before all three receipts; do not restart automatically')
   if len(rows)<6:time.sleep(15)
 passed=all(r['exit_status']==0 for r in rows)
 for row in rows:
  if row['exit_status']==0:
   v=json.loads(pathlib.Path(row['verification']).read_text());assert v['all_soft_policy_queries_xml_fraction_rc_caps_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and v['original_budget_gate_claimed'] is False;bindings[row['verification']]=sha(row['verification'])
 result=dict(status='pass' if passed else 'failed',all3_soft_policy_frames_and_all331800_events_pass=passed,bindings=bindings,rows=rows,original_budget_gate_claimed=False,scope='New soft-policy cap/physical/transaction audits only; no original hard timing gate, native STA, forecast quality or utility claim.')
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('SOFT_AUDIT_TERMINAL',passed,flush=True)
if __name__=='__main__':main()
