"""Existing capacity-bound head on frozen repaired frames, original controls/gates."""
import json,sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from evaluate_external_capacity_bounded_score_case_v1 import evaluate
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_primary_budget_repair_bounded_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 p=read(D/'protocol.json');assert all(sha(q)==h for q,h in p['bindings'].items());bindings={**p['bindings'],str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for c in p['cases']:
  out=Path(c['output']);out.mkdir(parents=True,exist_ok=False);spec=read(c['original_comparison_spec']);spec['schema']='ROUTECAST_EXTERNAL_CAPACITY_BOUNDED_UTILIZATION_SCORE_CASE_V1';spec['predictions']['native_retained_on']=dict(frame=c['candidate_frame'],proof=c['candidate_proof']);sp=out/'comparison_spec.json';sp.write_text(json.dumps(spec,indent=2)+'\n');rp=out/'comparison.json';evaluate(sp,rp);r=read(rp);rows.append(dict(case=c['case'],process_exit=0,original_case_gate=r['pass_case_gate'],metrics={m:{scope:{k:v[k] for k in ['spearman','top_k_hits','k','universe_size']} for scope,v in scopes.items()} for m,scopes in r['metrics'].items()},checks=r['checks']));bindings[str(sp)]=sha(sp);bindings[str(rp)]=sha(rp);print(json.dumps(rows[-1]),flush=True)
 assert all(sha(q)==h for q,h in bindings.items())
 with (D/'quality_summary.json').open('x') as f:json.dump(dict(status='ALL3_FROZEN_PRIMARY_REPAIR_BOUNDED_HEAD_EVALUATED',rows=rows,bindings=bindings,unavailable_cases=p['unavailable_cases'],all9_availability_pass=False),f,indent=2)
if __name__=='__main__':main()
