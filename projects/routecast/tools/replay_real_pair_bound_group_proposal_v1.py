"""All3 archived target-free pair revalidation and fresh group-vacancy proposals."""
import json,sys,hashlib
from pathlib import Path
from types import SimpleNamespace
from collections import defaultdict
from array import array
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from class_cached_rc_endpoint_context_v1 import load_endpoints
from bound_enabled_group_graph_v1 import bind
from compact_target_raw_bounds_v1 import CompactReverseBounds
from reverse_raw_delay_bounds_v1 import ReverseBounds
from group_vacancy_proposal_v4 import Snapshot,prepare,propose
E=R/'experiments';A=E/'prospective_external_family_fixed_nominal_ablation_v1_2026-10-19';P=E/'prospective_external_family_fixed_nominal_pair_exchange_v1_2026-10-19';I=E/'prospective_external_family_rejected_candidate_groups_v1_2026-10-20';D=E/'prospective_external_family_bound_pair_group_proposal_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def encode(value):
 if isinstance(value,(set,frozenset)):return sorted(value)
 return str(value)
def main():
 proof=read(I/'research_decision_v1.json');assert all(sha(p)==h for p,h in proof['bindings'].items());contract=E/'bound_enabled_group_proposal_contract_v1_2026-10-20/verification.json';assert all(sha(p)==h for p,h in read(contract)['bindings'].items());D.mkdir(exist_ok=False);cases=read(A/'protocol.json')['cases'];bindings={str(I/'research_decision_v1.json'):sha(I/'research_decision_v1.json'),str(contract):sha(contract),str(Path(__file__).resolve()):sha(__file__),str(R/'tools/group_vacancy_proposal_v4.py'):sha(R/'tools/group_vacancy_proposal_v4.py')};(D/'protocol.json').write_text(json.dumps(dict(cases=[c['case'] for c in cases],policy='All3 same prior target-free pair3279/3280. Revalidate actual archived candidates and raw budgets through pure group API; independently frozen snapshot used for fresh numeric-NET-order group vacancy search,10000 labels. No shared-state/epoch writes, labels, commit, per-case selection or forecast gain claim.'),indent=2)+'\n');rows=[]
 for c in cases:
  case=c['case'];out=A/case/'native_retained/warm_timing_round_updated';frame=read(out/'round1.json');receipt=read(out/'receipt.json');pair=read(P/case/'feasible_pairs.json');assert len(pair)==1;members=pair[0]['nets'];graph,digest,nodes,f,rc,queries=load_endpoints(c['endpoint']);qs=defaultdict(list);old=defaultdict(list)
  for q in queries:
   if q['net_id'] in members:qs[q['net_id']].append(q)
  for q in frame['records']:
   if q['net_id'] in members:old[q['net_id']].append(q)
  candidate={event['net_id']:event['rejected_records'] for event in receipt['rounds'][1]['events'] if event['net_id'] in members};ledger={int(n):v for n,v in frame['ledger'].items()};crit={q['connection_id']:q for q in read(out/'timing_round1.json')['criticalities']};basefile=Path(c['node_base_proof']).parent/'node_base.u64';base=array('Q');base.frombytes(basefile.read_bytes());spans={i:max(int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow')),int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')))+1 for i,n in enumerate(nodes) if n.get('type') in ('CHANX','CHANY')};history={int(n):v-spans.get(int(n),0) for n,v in frame['prices'].items()};slots={eid:i for i,eid in enumerate(f['edge_ids'])};before=sha(out/'round1.json');snapshot=Snapshot(f,rc,slots,dict(qs),dict(old),ledger,crit,base,history,spans,rc.scale//(20*10**9));plan=prepare(snapshot,candidate);assert plan['accepted'] and plan['prospective_overflow_delta']==0 and str(plan['objective_delta'])=='-2368259765625/32768';original=SimpleNamespace(n=len(f['capacities']),offsets=f['row_offsets'],dest=f['dest_ranks'],inc=rc.increments,initial=tuple(rc.initial(i) for i in range(len(f['capacities']))),repair_bounds=None);compact=CompactReverseBounds(original.offsets,original.dest,original.inc);legacy=ReverseBounds(original.offsets,original.dest,original.inc);fresh,meta=propose(snapshot,bind(original,compact),10000);legacy_candidate,legacy_meta=propose(snapshot,bind(original,legacy),10000);assert fresh==legacy_candidate and meta==legacy_meta;assert sha(out/'round1.json')==before and ledger=={int(n):v for n,v in frame['ledger'].items()};dest=D/case;dest.mkdir(parents=True);payload=dest/'proposal.json';payload.write_text(json.dumps(dict(members=members,archived_candidate=candidate,archived_plan=plan,fresh_candidate=fresh,fresh_metadata=meta,compact_stats=compact.stats(),legacy_transcript_equal=True),default=encode)+'\n');row=dict(case=case,members=members,archived_pair_API_accepted=plan['accepted'],archived_pair_pressure_delta=plan['prospective_overflow_delta'],archived_pair_objective_delta=str(plan['objective_delta']),fresh_status=meta['status'],fresh_accepted=meta.get('plan',{}).get('accepted'),fresh_pressure_delta=meta.get('plan',{}).get('prospective_overflow_delta'),fresh_objective_delta=str(meta.get('plan',{}).get('objective_delta')),shared_input_file_unchanged=True);rows.append(row);print(json.dumps(row),flush=True)
  for p in [payload,out/'round1.json',out/'receipt.json',out/'timing_round1.json',basefile,Path(c['endpoint'])]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_REAL_PAIR_BOUND_GROUP_API_LEGACY_COMPACT_TRANSCRIPT_PARITY_PASS',rows=rows,bindings=bindings,scope='Read-only pair proof and bound-enabled fresh proposals; complete compact-v-legacy transcript parity, no zero-v-bound parity or performance/forecast claim.'),indent=2)+'\n')
if __name__=='__main__':main()
