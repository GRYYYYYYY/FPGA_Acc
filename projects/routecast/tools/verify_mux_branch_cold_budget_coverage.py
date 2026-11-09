"""Independent backward cold-delay transfer and numeric budget inventory."""
import json
from pathlib import Path
from fractions import Fraction as F
from functools import lru_cache
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_branch_cold_budget_coverage_2026-10-06';file=out/'receipt.json';d=json.loads(file.read_text());assert all(sha(f)==h for f,h in d['bindings'].items());base=ROOT/'experiments/mux_bounded_branch_online_loop_2026-10-06';cold=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06';assert d['protocol_sha256']==sha(base/'protocol.json') and d['cold_receipt_sha256']==sha(cold/'receipt.json') and d['cold_verification_sha256']==sha(cold/'verification.json');native={(r['width'],r['index']):r for r in json.loads((cold/'receipt.json').read_text())['rows']}
for row in d['rows']:
 w,i=row['width'],row['index'];sf=cold/f'mux_w{w}_m{i}_0/accepted_state.json';assert sha(sf)==native[w,i]['rounds'][0]['snapshot_sha256'];state=json.loads(sf.read_text());delays={str(r['connection_id']):F(r['answer']['delay']*10**9,state['scale']) for r in state['records']};a=json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text());tg=json.loads((ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json').read_text());mapping=json.loads((ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json').read_text());incoming={int(n):[] for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 @lru_cache(None)
 def arrival(n):return max([F(0)]+[arrival(u)+(delays[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
 cpd=max(arrival(int(n)) for n,k in tg['nodes'].items() if k=='SINK');printed=F(str(native[w,i]['rounds'][0]['native']['cpd_ns']));assert cpd==F(row['cold_model_cpd_ns']) and printed==F(row['cold_native_printed_cpd_ns']);assert abs(cpd-printed)<=F('0.00001');assert row['cold_model_meets_target']==(cpd<=F(a['target_cpd_ns'])) and row['cold_native_printed_meets_target']==(printed<=F(a['target_cpd_ns']))
 actual=json.loads((base/f'w{w}_m{i}/result.json').read_text())
 for attempt,coverage in zip(actual['attempts'],row['allocations']):
  spec=actual['allocations'][attempt['allocation_index']];violations=sorted(int(cid) for cid,value in delays.items() if value>F(spec['budgets_ns'][cid]));assert coverage['allocation_index']==spec['index'] and sorted(coverage['connections_exceeding_budget'])==violations and coverage['expanded_exceeding']==sum(cid in spec['expanded'] for cid in violations)
 assert len(actual['attempts'])==len(row['allocations'])
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(file),verifier_sha256=sha(Path(__file__)),cases=len(d['rows']),scope='Independent backward wholeDAG CPD versus forward producer; accepted cold snapshot hashes and printed-native parity within1e-5ns, exact numeric allocation coverage. Different global/frozen/exclusion route spaces remain; no identical-space false rejection/nativeSTA invariant proof.'),indent=2)+'\n');print('verified cold transfer/coverage',len(d['rows']))
