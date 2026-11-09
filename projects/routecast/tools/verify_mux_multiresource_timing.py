"""Full old-DAG floor feasibility for every two-resource detour option."""
import json
from collections import defaultdict,deque
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_multiresource_options_2026-10-06';r=json.loads((out/'receipt.json').read_text());v=json.loads((out/'verification.json').read_text());assert v['receipt_sha256']==sha(out/'receipt.json');rows=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':rows.append(row);continue
 w,i=row['width'],row['index'];d=json.loads((out/f'w{w}_m{i}.json').read_text());af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(af.read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mp=json.loads(mf.read_text());adj=defaultdict(list);indegree={int(n):0 for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:adj[e['source']].append((e['sink'],eid));indegree[e['sink']]+=1
 queue=deque(n for n,c in indegree.items() if not c);order=[]
 while queue:
  u=queue.popleft();order.append(u)
  for sink,eid in adj[u]:
   indegree[sink]-=1
   if not indegree[sink]:queue.append(sink)
 assert len(order)==len(indegree)
 options=[]
 for option in d['options']:
  floor={cid:F(x) for cid,x in a['floor_ns'].items()};supported=True;cap_ok=True
  for ans in option['answers']:
   cid=str(ans['query']['connection_id'])
   if ans['minimum'] is None:supported=False;continue
   floor[cid]=max(floor[cid],F(ans['minimum']*10**9,d['scale']));cap_ok=cap_ok and floor[cid]<=1
  arrival={n:F(0) for n in order}
  for u in order:
   for sink,eid in adj[u]:
    delay=floor[str(a['edge_connection_ids'][eid])]+F(mp['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9
    arrival[sink]=max(arrival[sink],arrival[u]+delay)
  cpd=max(arrival[int(n)] for n,kind in tg['nodes'].items() if kind=='SINK');target=F(a['target_cpd_ns']);options.append(dict(chosen_net=option['chosen_net'],restrictions=option['restrictions'],model_floor_cpd_ns=str(cpd),target_cpd_ns=str(target),cap_ok=cap_ok,feasible=supported and cap_ok and cpd<=target))
 rows.append(dict(width=w,index=i,options=options,any_feasible=any(o['feasible'] for o in options)))
expected=json.loads((out/'timing_options.json').read_text());assert rows==expected['rows'] and expected['receipt_sha256']==sha(out/'receipt.json')
(out/'timing_options_verification.json').write_text(json.dumps(dict(timing_sha256=sha(out/'timing_options.json'),receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent forward topological rational recurrence versus backward evaluator for all14 options, including floor/cap/status. Shared input/model mappings; no native STA/capacity realization.'),indent=2)+'\n');print('all14 full timing options independently verified')
