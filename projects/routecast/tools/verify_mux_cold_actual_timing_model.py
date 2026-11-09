"""Independent backward evaluation of actual accepted cold delay vectors."""
import json
from pathlib import Path
from collections import defaultdict,deque
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_cold_actual_timing_model_2026-10-07';r=json.loads((out/'receipt.json').read_text());assert all(sha(f)==h for f,h in r['bindings'].items());cold=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06';original=json.loads((cold/'receipt.json').read_text());assert len(r['rows'])==len(original['rows'])==12
for row,old in zip(r['rows'],original['rows']):
 w,i=row['width'],row['index'];assert (w,i)==(old['width'],old['index']);s=json.loads((cold/f'mux_w{w}_m{i}_0/accepted_state.json').read_text());actual={str(q['connection_id']):F(q['answer']['delay']*10**9,s['scale']) for q in s['records']};g=json.loads((ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json').read_text());m=json.loads((ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json').read_text());a=json.loads((ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json').read_text());adj=defaultdict(list);ind={int(n):0 for n in g['nodes']}
 for eid,e in g['edges'].items():
  if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 queue=deque(n for n in ind if not ind[n]);order=[]
 while queue:
  u=queue.popleft();order.append(u)
  for v,eid in adj[u]:
   ind[v]-=1
   if not ind[v]:queue.append(v)
 assert len(order)==len(ind);tail={n:F(0) for n in order}
 for u in reversed(order):
  for v,eid in adj[u]:
   cid=a['edge_connection_ids'].get(eid);delay=actual[str(cid)]+F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9 if cid is not None else F(g['edges'][eid]['max_delay_seconds'])*10**9;tail[u]=max(tail[u],delay+tail[v])
 cpd=max(tail.values());native=F(str(old['rounds'][0]['reload']['cpd_ns']));assert cpd==F(row['actual_model_cpd_ns']) and native==F(row['accepted_native_cpd_ns']);assert cpd-native==F(row['model_minus_native_ns']);assert row['model_target_pass']==(cpd<=F(row['target_ns'])) and row['native_target_pass']==(native<=F(row['target_ns']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),source_sha256=sha(Path(__file__)),cases=12,maximum_absolute_difference_ns=str(max(abs(F(x['model_minus_native_ns'])) for x in r['rows'])),target_classification_matches=sum(x['model_target_pass']==x['native_target_pass'] for x in r['rows']),scope='Independent backward versus forward exact DAG evaluation, authenticated accepted cold snapshot/native rounded CPD bindings. Existing original-XML/native proof reused; not new native execution or universal model guarantee.'),indent=2)+'\n');print('Verified all12 backward-DAG values and native comparisons',flush=True)
