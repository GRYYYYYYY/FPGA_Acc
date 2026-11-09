"""Authenticated recorded lineage cost, explicitly not a matched lifecycle run."""
import json
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
names=['mux32_critical_repair','mux32_incremental_budget_tree','mux32_reverse_tree','mux32_longest_first_tree','mux32_shortest_first_tree','mux32_id_revisit_tree','mux32_limit_retry_tree']
rows=[];bindings={};previous=None
for name in names:
 base=ROOT/'experiments'/(name+'_2026-10-07');rp=base/'receipt.json';pp=base/'protocol.json';cp=base/'candidate.json';vp=base/'verification.json'
 r=json.loads(rp.read_text());p=json.loads(pp.read_text());v=json.loads(vp.read_text())
 assert r['protocol_sha256']==sha(pp) and r['candidate_sha256']==sha(cp) and v['receipt_sha256']==sha(rp)
 assert all(sha(f)==h for f,h in {**p['sources'],**p['inputs']}.items())
 if previous is not None:assert p['inputs'][str(previous)]==sha(previous)
 else:
  seed=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/w32_m2/result.json'
  assert p['inputs'][str(seed)]==sha(seed)
 previous=cp
 bindings.update({str(f):sha(f) for f in (rp,pp,cp,vp)})
 rows.append(dict(stage=name,input_candidate='prepared seed' if len(rows)==0 else names[len(rows)-1],producer_seconds=str(r['producer_seconds']),wirelength=v['channel_union_wirelength'],cpd_ns=r['final_cpd_ns']))
native=ROOT/'experiments/mux32_limit_retry_native_2026-10-07';canonical=ROOT/'experiments/mux32_limit_retry_canonical_2026-10-07'
for base in (native,canonical):
 rp=base/'receipt.json';vp=base/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert v['receipt_sha256']==sha(rp)
 bindings.update({str(f):sha(f) for f in (rp,vp)})
 rows.append(dict(stage=base.name,producer_seconds=str(r['seconds']),wirelength=11883,cpd_ns='2.87349'))
join=canonical/'state_join_verification.json';j=json.loads(join.read_text());assert all(sha(f)==h for f,h in j['bindings'].items());bindings[str(join)]=sha(join)
search=sum((Decimal(x['producer_seconds']) for x in rows[:7]),Decimal(0));total=sum((Decimal(x['producer_seconds']) for x in rows),Decimal(0))
result=dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,recorded_lineage_search_seconds=str(search),recorded_search_plus_final_native_canonical_seconds=str(total),excluded=['Initial prepared predictor/seed production, endpoint/RR/timing conversions','Independent proofs and all extra native evaluations between search rounds','Alternative development runs excluded from selected candidate ancestry','Idle gaps, orchestration and raw-input frontend/compiler costs'],scope='Arithmetic sum of recorded ancestor process component clocks in separate runs, NOT a continuous full-workflow or stable performance measurement. Establishes hidden ancestor costs for this selected development artifact. No matched baseline, prospective result or complete netgain.')
out=ROOT/'experiments/mux32_candidate_lineage_cost_2026-10-07';out.mkdir(exist_ok=True);(out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(search,total)
