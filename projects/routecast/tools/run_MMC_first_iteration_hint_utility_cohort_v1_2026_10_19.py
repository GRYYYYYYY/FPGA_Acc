"""Fixed6 jobs after actual semantic admission; retain every native/audit failure."""
import pathlib,json,hashlib,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def main():
 P=R/'experiments/mmc_first_iteration_hint_utility_protocol_v1_2026-10-19/protocol.json';spec=json.loads(P.read_text());ap=pathlib.Path(spec['semantic_admission']);a=json.loads(ap.read_text());assert a['all3_utility_trial_semantically_admitted'];assert a['status']=='ACTUAL_FIRST_ITERATION_HINT_EXPIRY_BITS_AND_ZERO_ABSENT_NATIVE_EQUIVALENCE_PASS'
 for doc in [spec,a]:
  for p,h in doc['bindings'].items():assert sha(pathlib.Path(p))==h
 assert [(x['case'],x['arm']) for x in spec['jobs']]==[(f'episode_{i:02d}',arm) for i in range(1,4) for arm in ['zero','forecast']]
 if '--check-only' in sys.argv:print('FIRST_ITERATION_HINT_ALL6_INPUTS_AND_ACTUAL_SEMANTICS_ADMITTED');return
 O=R/'experiments/mmc_first_iteration_hint_utility_v1_2026-10-19';O.mkdir(exist_ok=False);runner=R/'tools/run_MMC_first_iteration_hint_utility_case_v1_2026_10_19.py';bindings={**spec['bindings'],str(P):sha(P),str(ap):sha(ap),str(pathlib.Path(__file__).resolve()):sha(pathlib.Path(__file__).resolve())};write(O/'input_admission.json',dict(bindings=bindings,all_inputs_and_zero_equivalence_admitted=True,scope='Actual zero/absent and expiry semantics admitted, no prediction/utility/heldout success.'))
 I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';rows=[]
 for job in spec['jobs']:
  case,arm=job['case'],job['arm'];parent=O/case;parent.mkdir(exist_ok=True);print('FIRST_HINT_UTILITY_START',case,arm,flush=True)
  with (parent/(arm+'.log')).open('x') as log:
   child=subprocess.Popen([sys.executable,str(runner),str(I/case),str(parent/arm),arm],cwd=R,stdout=log,stderr=subprocess.STDOUT);write(O/'live_case_process.json',dict(pid=child.pid,startticks=pathlib.Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()[19],case=case,arm=arm));code=child.wait()
  row=dict(case=case,arm=arm,exit_code=code);rows.append(row);write(parent/(arm+'_execution.json'),row);write(O/'progress.json',dict(terminal_jobs=rows));print('FIRST_HINT_UTILITY_TERMINAL',row,flush=True)
  # Do not prune exposed cases after an unfavorable utility or audit result.
 write(O/'terminal.json',dict(status='ALL6_NATIVE_READBACK_PHYSICAL_CANONICAL_PASS' if all(x['exit_code']==0 for x in rows) else 'ALL6_TERMINAL_FAILURES_PRESERVED',rows=rows,independent_native_work_and_utility_gate_pending=True,complete_workflow_gain_proven=False))
if __name__=='__main__':main()
