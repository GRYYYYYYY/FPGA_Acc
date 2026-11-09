"""Frozen-width native diagnostic cohort; finite-budget failure is not infeasibility."""
import json,os,subprocess,shutil,time,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];src=R/'experiments/sha1_actual_old_linear_expat_workflow_v1_2026-10-10';vp=src/'verification.json';v=json.loads(vp.read_text());assert v['all_cases_both_complete_arms_authenticated'] and all(sha(k)==h for k,h in v['bindings'].items())
native=src/'cold/native/sha1';rp=native/'receipt.json';r=json.loads(rp.read_text());D=R/'experiments/sha1_native_width_cohort_v1_2026-10-10';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__)),str(vp):sha(vp),str(rp):sha(rp)};cases=[]
for width in [32,64,96]:
 w=D/str(width);w.mkdir()
 for f in ['design.blif','design.net','design.place']:shutil.copyfile(native/f,w/f);bindings[str(native/f)]=sha(native/f);bindings[str(w/f)]=sha(w/f)
 cmd=r['command'].copy();i=cmd.index('--read_rr_graph');del cmd[i:i+2];cmd[cmd.index('--route_chan_width')+1]=str(width);cmd+=['--write_rr_graph','rr_graph.xml']
 for p in [Path(cmd[0]),Path(cmd[1])]:bindings[str(p)]=sha(p)
 cases.append(dict(width=width,command=cmd))
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,timeout_per_case_seconds=300,scope='Widths32/64/96 frozen before cohort execution; original fixed placement/HDL/experimental architecture, same one-worker/seed1/max100/FULL cold settings, new per-width RR graph. All cases run once; timeout and input/export failure distinct from finite-budget native routing failure; no mathematical infeasibility/strict heldout/full-cost gain/real timing claim. Prior width128 results known. No seed or predictor in these labels.'),indent=2)+'\n');rows=[]
for case in cases:
 w=D/str(case['width']);t=time.perf_counter()
 with (w/'native.log').open('w') as log:
  try:code=subprocess.run(case['command'],cwd=w,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=300).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 text=(w/'native.log').read_text();status='UNCLASSIFIED_NATIVE_EXIT'
 if code=='TIMEOUT':status='TIMEOUT'
 elif code==0 and 'VPR succeeded' in text and 'Successfully routed after' in text:status='ROUTE_SUCCESS_PENDING_PHYSICAL_AUDIT'
 elif 'Routing failed.' in text:status='FINITE_BUDGET_ROUTE_FAILURE_PENDING_CLASSIFICATION_AUDIT'
 rows.append(dict(width=case['width'],exit_code=code,status=status,instrumented_process_seconds=time.perf_counter()-t,files={str(p):sha(p) for p in w.iterdir() if p.is_file()}));(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(case['width'],status,code,flush=True)
assert all(sha(k)==h for k,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_cases_attempted=len(rows)==3,all_labels_independently_verified=False),indent=2)+'\n')
