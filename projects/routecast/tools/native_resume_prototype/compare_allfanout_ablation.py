"""Compare altered router policies without hiding changes to cold reference."""
import json,sys
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
op=ROOT/'experiments/native_resume_precritical_cohort_2026-10-07/verification.json';np=ROOT/'experiments/native_resume_allfanout_cohort_2026-10-07/verification.json'
o,n=[json.loads(p.read_text()) for p in (op,np)]
bindings={str(p):sha(p) for p in (op,np,Path(__file__))}
for report in (o,n):
 assert all(sha(p)==h for p,h in report['bindings'].items())
old={(r['width'],r['index']):r for r in o['rows']};rows=[]
for new in n['rows']:
 key=new['width'],new['index'];before=old[key]
 if not new['complete'] or not before['complete']:
  rows.append(dict(width=key[0],index=key[1],complete=False));continue
 # Same target hash across arms; different cold policy reported explicitly.
 root_old=ROOT/f'experiments/native_resume_cohort_w{key[0]}_m{key[1]}_workflow_2026-10-07'
 root_new=ROOT/f'experiments/native_resume_allfanout_w{key[0]}_m{key[1]}_workflow_2026-10-07'
 a,b=[json.loads((root/'protocol.json').read_text()) for root in (root_old,root_new)]
 shared=set(a['inputs'])&set(b['inputs']);assert all(a['inputs'][p]==b['inputs'][p] for p in shared)
 for root in (root_old,root_new):bindings[str(root/'protocol.json')]=sha(root/'protocol.json')
 native_delta=F(new['cpd_pair'][0])-F(before['cpd_pair'][0]);cold_delta=F(new['cpd_pair'][1])-F(before['cpd_pair'][1])
 new_vs_originalcold=F(new['cpd_pair'][0])<=F(before['cpd_pair'][1]) and new['wire_pair'][0]<=before['wire_pair'][1]
 rows.append(dict(width=key[0],index=key[1],complete=True,default_joint_pass=before['joint_nonregression'],allfanout_matched_joint_pass=new['joint_nonregression'],allfanout_vs_original_default_cold_joint_pass=new_vs_originalcold,resume_cpd_change_ns=str(native_delta),cold_cpd_change_ns=str(cold_delta),resume_wire_change=new['wire_pair'][0]-before['wire_pair'][0],cold_wire_change=new['wire_pair'][1]-before['wire_pair'][1],default_cpd_pair=before['cpd_pair'],allfanout_cpd_pair=new['cpd_pair'],default_wire_pair=before['wire_pair'],allfanout_wire_pair=new['wire_pair'],default_connection_attempts=[before['workflow_work']['rerouted_connection_attempts'],before['cold_work']['rerouted_connection_attempts']],allfanout_connection_attempts=[new['workflow_work']['rerouted_connection_attempts'],new['cold_work']['rerouted_connection_attempts']]))
result=dict(bindings=bindings,rows=rows,default_quality_passes=o['quality_passes'],allfanout_quality_passes=n['quality_passes'],allfanout_vs_originalcold_passes=sum(r.get('allfanout_vs_original_default_cold_joint_pass',False) for r in rows),default_total_time_ratio=o['aggregate_ratio'],allfanout_total_time_ratio=n['aggregate_ratio'],scope='Two-factor policy ablation minfanout16->0 and AUTO->ON, effects not individually identifiable. All12 existing development moves, matched policy cold comparison plus original default cold quality. Old/new timing observations separate serial runs, not stable speedup inference. No cost-free selecting arm per target/native label, accepted fallback workflow or heldout.')
out=ROOT/'experiments/native_resume_allfanout_ablation_2026-10-07';out.mkdir(exist_ok=False)
(out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print([(r['width'],r['index'],r.get('default_joint_pass'),r.get('allfanout_matched_joint_pass'),r.get('allfanout_vs_original_default_cold_joint_pass'),r.get('resume_wire_change')) for r in rows]);print({k:result[k] for k in ('default_quality_passes','allfanout_quality_passes','allfanout_vs_originalcold_passes','allfanout_total_time_ratio')})
