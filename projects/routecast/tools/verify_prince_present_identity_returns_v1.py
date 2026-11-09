"""Native identity-return coverage plus exact event/context parity with ledger baseline."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_present_identity_trial_v1_2026-10-20';OLD=R/'experiments/prince_ownership_ledger_trial_v2_2026-10-20'
def main():
 p=D/'verification.json';v=json.loads(p.read_text());priorp=OLD/'ledger_verification_v1.json';prior=json.loads(priorp.read_text());bindings={str(p):sha(p),str(priorp):sha(priorp),str(__file__):sha(__file__)};rows=[]
 assert len(v['rows'])==18
 for row in v['rows']:
  case=row['case'];d=D/case;modep=d/'consumer_mode.json';mode=json.loads(modep.read_text());assert mode['conditional_present_identity_return']==case.endswith('/capture');assert sha(modep)==row['files'][str(modep)];bindings[str(modep)]=sha(modep)
  if not case.endswith('/capture'):assert not (d/'queries.tsv').exists();continue
  qp=d/'queries.tsv';old=OLD/case/'queries.tsv';a=[list(map(int,s.split())) for s in qp.read_text().splitlines()];b=[list(map(int,s.split())) for s in old.read_text().splitlines()];assert len(a)==len(b)==row['iterations'];assert all(len(x)==6 and x[:5]==y and x[5]==x[2] for x,y in zip(a,b));returned=sum(x[5] for x in a);assert returned>0
  for name in ['queries.tsv.ledger.bin','queries.tsv.connections.tsv']:
   ap=d/name;bp=OLD/case/name;h=sha(ap);assert h==row['files'][str(ap)]==sha(bp)==prior['bindings'][str(bp)];bindings[str(ap)]=h;bindings[str(bp)]=h
  for path in [qp,old]:bindings[str(path)]=sha(path)
  rows.append(dict(case=case.rsplit('/',1)[0],native_cost_calls=sum(x[1] for x in a),CHANNEL_costs_returned_from_conditional_identity=returned,bit_equality_asserted_calls=returned,all_phase_query_order_digests_equal=True,event_and_connection_bytes_equal=True))
 assert len(rows)==9 and sum(x['CHANNEL_costs_returned_from_conditional_identity'] for x in rows)==65427087;assert all(sha(p)==h for p,h in bindings.items());out=D/'identity_return_verification_v1.json';assert not out.exists();out.write_text(json.dumps(dict(status='ALL_OBSERVED_CHANNEL_COSTS_RETURNED_BY_BIT_EXACT_IDENTITY_CONSUMER',rows=rows,bindings=bindings,limitations=['Original cost computed once for comparison, then recomputed identity value returned for CHANNELs. This duplicates scalar work and proves no speed benefit.','Unsupported CHANNEL capacity/nonconfigurable groups fail closed; nonCHANNEL costs forwarded. No future-demand predictor.','Scope is observed linker-visible calls in pinned serial cohort.']),indent=2)+'\n');print('NATIVE_IDENTITY_RETURN_PASS',sum(x['CHANNEL_costs_returned_from_conditional_identity'] for x in rows))
if __name__=='__main__':main()
