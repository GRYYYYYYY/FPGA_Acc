"""Compare all four fixed tolerance controls and their nonsemantic force traces."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_tol101_controls_2026-10-07'
oldfile=ROOT/'experiments/native_resume_cbrrfix_controls_2026-10-07/verification.json';newfile=out/'verification.json';tracefile=ROOT/'experiments/native_resume_cbrr_tol101_force_audit_2026-10-07/receipt.json'
a,b,t=[json.loads(f.read_text()) for f in (oldfile,newfile,tracefile)]
for d in (a,b):assert all(sha(f)==h for f,h in d['bindings'].items())
rows=[]
for tr in t['rows']:
 assert all(sha(f)==h for f,h in tr['files'].items())
 w,i,mode=tr['width'],tr['index'],tr['mode'];paths=[]
 for policy in ('cbrrfix','tol101'):
  f=ROOT/f'experiments/native_resume_{policy}_w{w}_m{i}_{mode}_2026-10-07/first/output.route';paths.append({n:Counter(ps) for n,ps in physical_paths(f).items() if ps})
 select=[x for x in tr['events'] if x[0]=='RC_FORCE_SELECT']
 rows.append(dict(width=w,index=i,mode=mode,all_named_paths_equal_previous_policy=paths[0]==paths[1],selected_events=len(select),selected_by_net=dict(Counter(x[2] for x in select)),s6_0_pin9_selections=sum(x[2]=='s6_0' and x[3]=='9' for x in select)))
result=dict(bindings={str(f):sha(f) for f in (oldfile,newfile,tracefile,Path(__file__))},rows=rows,new_quality_passes=b['quality_passes'],new_aggregate_ratio=b['aggregate_ratio'],scope='Development two-case ablation, one cost pair per case. Both policy-matched controls, no filtering of quality failures. Forced selections do not prove path improvement; archived full-path parity shows repeated selections can return same paths.')
a_paths=physical_paths(ROOT/'experiments/native_resume_cbrrfix_w16_m1_workflow_2026-10-07/first/output.route');b_paths=physical_paths(ROOT/'experiments/native_resume_tol101_w16_m1_workflow_2026-10-07/first/output.route')
branch=lambda x:[p for p in x['s6_0'] if p[-1][0]==4018]
assert len(branch(a_paths))==len(branch(b_paths))==1
result['w16_s6_0_sink4018_final_path_equal_previous']=branch(a_paths)==branch(b_paths)
(out/'ablation_comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
