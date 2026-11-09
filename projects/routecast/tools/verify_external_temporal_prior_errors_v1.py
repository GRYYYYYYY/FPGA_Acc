"""Verify disjoint all-ID partitions against certified frame and score identities."""
import json,sys
from pathlib import Path
from fractions import Fraction as F
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_temporal_prior_errors_v1_2026-10-19';T=R/'experiments/prospective_external_family_temporal_prior_utilization_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 summary=read(D/'summary.json');assert all(sha(p)==h for p,h in summary['bindings'].items());cases=read(D/'protocol.json')['cases'];rows=[]
 for c,published in zip(cases,summary['rows']):
  assert c['case']==published['case'];s=read(c['original_comparison_spec']);old=read(c['source_frame']);new=read(c['current_frame']);label=read(s['label_physical_audit']);domain=Path(s['domain_proof']).parent;ids={json.loads(x)['id'] for x in (domain/'resources.jsonl').read_text().splitlines()};scores={n:F(*v) for n,v in read(T/c['case']/'comparison.json')['score_vectors']['resource']};seen=set();counts=Counter();errors=defaultdict(F)
  for line in (D/c['case']/'resources.jsonl').read_text().splitlines():
   r=json.loads(line);n=r['id'];assert n in ids and n not in seen;seen.add(n);assert r['old']==int(old['ledger'].get(str(n),0)>0) and r['current']==int(new['ledger'].get(str(n),0)>0) and r['truth']==int(label['node_occupancy'].get(str(n),0)>0);score=F(*r['score']);assert score==scores[n];delta=(score-r['truth'])**2-(r['old']-r['truth'])**2;assert delta==F(*r['squared_error_delta']);key=(r['old'],r['current'],r['truth'],r['edit_mask']);counts[key]+=1;errors[key]+=delta
  assert seen==ids and sum(counts.values())==published['resource_rows']==45584
  assert {(x['old'],x['current'],x['truth'],x['edit_mask']):(x['count'],F(*x['squared_error_delta'])) for x in published['cells']}=={k:(v,errors[k]) for k,v in counts.items()}
  assert sum(errors.values(),F(0))==F(*published['total_squared_error_delta'])
  # Independently validate NET edit classes from endpoint identity, no label use.
  grouped=[]
  for frame in [old,new]:
   by=defaultdict(dict)
   for q in frame['records']:by[q['net_id']][q['connection_id']]=q
   grouped.append(by)
  kinds=Counter()
  for r in read(D/c['case']/'NETs.json'):
   a,b=(v[r['net_id']] for v in grouped);sc=any(a[k]['source']!=b[k]['source'] for k in a);sn=sum(a[k]['sink']!=b[k]['sink'] for k in a);kind=4 if sc and sn else 1 if sc else 2 if sn else 0;assert (r['edit_mask'],r['fanout'],r['source_changed'],r['changed_sinks'])==(kind,len(a),sc,sn);kinds[kind]+=1
  assert {str(k):v for k,v in kinds.items()}==published['edited_NET_counts'];rows.append(dict(case=c['case'],resources=len(ids),partition_cells=len(counts)))
 with (D/'independent_partition_verification_v1.json').open('x') as f:json.dump(dict(status='ALL136752_RESOURCE_IDENTITIES_SCORE_ERRORS_PARTITIONS_AND_NET_EDIT_CLASSES_VERIFIED',rows=rows,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Checks all-ID table identities against audited ledgers/exported independently verified scores, exact error sums and endpoint edit classes. Resource edit-mask support membership is producer-derived, not independently XML-reconstructed by this verifier.'),f,indent=2)
 print('ALL136752_ROWS_EXACT_PARTITIONS_VERIFIED')
if __name__=='__main__':main()
