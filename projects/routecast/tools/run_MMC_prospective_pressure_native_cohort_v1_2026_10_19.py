"""Fail-closed admission of all3 predictions before frozen native observations."""
import json,pathlib,sys,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 M=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19';I=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19';P=R/'experiments/mmc_prospective_pressure_protocol_v1_2026-10-19/protocol.json';O=R/'experiments/mmc_prospective_pressure_native_v1_2026-10-19';runner=R/'tools/run_MMC_prospective_pressure_native_case_v1_2026_10_19.py'
 terminal=M/'terminal.json'
 if not terminal.exists():raise SystemExit('NOT_READY: prediction pipeline has no terminal result; no native directory created')
 assert json.loads(terminal.read_text())['status']=='ALL_THREE_INITIALIZERS_AND_INDEPENDENT_AUDITS_PASS'
 spec=json.loads(P.read_text());bindings={str(P):sha(P),str(terminal):sha(terminal),str(runner):sha(runner),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for p,h in spec['bindings'].items():assert sha(p)==h,p;bindings[p]=h
 predictions=[]
 for name in spec['episodes']:
  p=M/name/'initial_independent_verification_v1.json';v=json.loads(p.read_text());assert v['status']=='pass' and v['all115572V2budgets_matched'];assert len(v['rows'])==2 and all(x['all_original_XML_fraction_paths_budgets_parents_ledgers_pass'] for x in v['rows'])
  for q,h in v['bindings'].items():assert sha(q)==h,q;bindings[q]=h
  bindings[str(p)]=sha(p)
  for mode in ['raw_min','native_retained']:
   q=M/name/mode/'initial.json';assert bindings[str(q)]==sha(q);predictions.append(dict(episode=name,model=mode,path=str(q),sha256=sha(q)))
 if '--check-only' in sys.argv:
  print('READY: all3 independent audits and prediction hashes verified; no routes launched');return
 assert not O.exists();O.mkdir()
 write(O/'prediction_admission.json',dict(bindings=bindings,predictions=predictions,all3_independent_prediction_audits_pass=True,strict_unseen_family_admitted=False,scope='All prediction bytes bound before any target route launch; no quality or timing claim.'))
 write(O/'execution_protocol.json',dict(bindings=bindings,commands=spec['native_commands'],order=spec['episodes'],max_concurrency=1,independent_trace_replay_pending=True))
 rows=[]
 for name in spec['episodes']:
  with (O/(name+'.log')).open('x') as f:code=subprocess.run([sys.executable,str(runner),str(I/name),str(O/name)],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  rows.append(dict(episode=name,exit_code=code));write(O/(name+'_execution.json'),rows[-1])
  if code:write(O/'terminal.json',dict(status='NATIVE_OR_AUDIT_FAILED',rows=rows));raise SystemExit(code)
 write(O/'terminal.json',dict(status='THREE_NATIVE_PHYSICAL_CANONICAL_PASS',rows=rows,independent_trace_replay_pending=True,forecast_quality_pending=True,complete_workflow_gain_pending=True))
if __name__=='__main__':main()
