"""Evaluate all frozen temporal-prior cases, keeping original admission and gates."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from evaluate_external_temporal_prior_score_case_v1 import evaluate
R=Path(__file__).resolve().parents[1]
D=R/'experiments/prospective_external_family_temporal_prior_utilization_v1_2026-10-19'
A=R/'experiments/prospective_external_family_budget_astar_reuse_warm_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=D/'protocol.json';protocol=read(p);bindings=closure([Path(__file__)]);bindings.update(protocol['bindings']);bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 proof=A/'independent_verification_v1.json';audit=read(proof)
 assert audit['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 assert all(sha(p)==h for p,h in audit['bindings'].items())
 rows=[]
 for c in protocol['cases']:
  frame=c['current_frame'];assert audit['bindings'][frame]==sha(frame)
  s=read(c['original_comparison_spec']);assert s['source_frame']==c['source_frame']
  s['schema']='ROUTECAST_EXTERNAL_TEMPORAL_PRIOR_SCORE_CASE_V1';s['predictions']['native_retained_on']=dict(frame=frame,proof=str(proof))
  out=D/c['case'];out.mkdir(parents=True,exist_ok=False);sp=out/'comparison_spec.json';sp.write_text(json.dumps(s,indent=2)+'\n');rp=out/'comparison.json';evaluate(sp,rp);d=read(rp)
  rows.append(dict(case=c['case'],pass_case_gate=d['pass_case_gate'],metrics={method:{scope:{k:v[k] for k in ['spearman','top_k_hits','k','universe_size']} for scope,v in m.items()} for method,m in d['metrics'].items()},checks=d['checks']))
  bindings[str(sp)]=sha(sp);bindings[str(rp)]=sha(rp);print(json.dumps(rows[-1]),flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 with (D/'quality_summary.json').open('x') as f:json.dump(dict(status='ALL3_FROZEN_TEMPORAL_PRIOR_CASES_EVALUATED',rows=rows,bindings=bindings,unavailable_cases=protocol['unavailable_cases'],all9_availability_pass=False),f,indent=2)
if __name__=='__main__':main()
