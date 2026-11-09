"""Oracle-free monotone wholeNET slack allocation from verified initial vectors."""
import json,time
from pathlib import Path
from collections import defaultdict,deque
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_critical_release_budgets_2026-10-06';out=ROOT/'experiments/mux_net_slack_budgets_2026-10-06';out.mkdir();p=json.loads((base/'protocol.json').read_text());verification=json.loads((base/'verification.json').read_text());assert verification['receipt_sha256']==sha(base/'receipt.json');protocol=dict(cases=p['cases'],base_receipt_sha256=sha(base/'receipt.json'),base_verification_sha256=sha(base/'verification.json'),source_sha256=sha(Path(__file__)),policy='No cold routes, archived conflicts or later outcomes. Same floors/wholeNET initial release cohort. Ascending NET ID, one pass: attempt raise all expanded NET connection budgets to1ns; if wholeDAG target exceeded use24 exact bisection steps from current vector towards1ns for that NET only. Other budgets unchanged, no shrink. Preparation timer separate, no routing/native acceptance proof.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for case in p['cases']:
 w,i=case['width'],case['index'];af=base/f'w{w}_m{i}.json';a=json.loads(af.read_text());file=out/f'w{w}_m{i}.json';start=time.perf_counter()
 if a['status']!='CRITICAL_RELEASE_VECTOR_CONSTRUCTED':
  file.write_text(json.dumps(dict(base_sha256=sha(af),status='PRIOR_ALLOCATION_SKIP'),indent=2)+'\n');rows.append(dict(width=w,index=i,status='PRIOR_ALLOCATION_SKIP',sha256=sha(file)))
 else:
  old=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';mapping_meta=json.loads(old.read_text());gf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(gf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(gf.read_text());mapping=json.loads(mf.read_text());adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
  for eid,e in tg['edges'].items():
   if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
  queue=deque(n for n,v in ind.items() if not v);order=[]
  while queue:
   u=queue.popleft();order.append(u)
   for v,eid in adj[u]:
    ind[v]-=1
    if not ind[v]:queue.append(v)
  assert len(order)==len(ind)
  def evaluate(b):
   arrival={n:F(0) for n in order}
   for u in order:
    for v,eid in adj[u]:
     delay=b[str(mapping_meta['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in mapping_meta['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9
     arrival[v]=max(arrival[v],arrival[u]+delay)
   return max(arrival[int(n)] for n,k in tg['nodes'].items() if k=='SINK')
  ep=json.loads(Path(case['target']).read_text());expanded=set(a['expanded_connection_ids']);groups=defaultdict(list)
  for q in ep['connections']:
   if q['connection_id'] in expanded:groups[q['net_id']].append(str(q['connection_id']))
  assert expanded=={q['connection_id'] for q in ep['connections'] if q['net_id'] in groups};budget={k:F(v) for k,v in a['budgets_ns'].items()};initial=dict(budget);target=F(a['target_cpd_ns']);assert evaluate(budget)==F(a['model_budget_cpd_ns'])<=target;trace=[]
  for net,cids in sorted(groups.items()):
   before=dict(budget);cap=dict(before)
   for cid in cids:cap[cid]=F(1)
   cap_cpd=evaluate(cap);low=F(1) if cap_cpd<=target else F(0)
   if low==1:budget=cap
   else:
    high=F(1)
    for _ in range(24):
     mid=(low+high)/2;trial=dict(before)
     for cid in cids:trial[cid]=before[cid]+mid*(1-before[cid])
     if evaluate(trial)<=target:budget=trial;low=mid
     else:high=mid
   trace.append(dict(net_id=net,connection_ids=sorted(map(int,cids)),alpha=str(low),cap_cpd_ns=str(cap_cpd),budget_cpd_ns=str(evaluate(budget))))
  assert all(budget[k]>=initial[k] for k in budget) and all(budget[str(cid)]<=1 for cid in expanded);cpd=evaluate(budget);assert cpd<=target
  file.write_text(json.dumps(dict(status='NET_SLACK_VECTOR_CONSTRUCTED',base_sha256=sha(af),old_metadata_sha256=sha(old),target_endpoint_sha256=sha(case['target']),initial_budgets_ns={k:str(v) for k,v in initial.items()},budgets_ns={k:str(v) for k,v in budget.items()},expanded_connection_ids=sorted(expanded),target_cpd_ns=str(target),model_budget_cpd_ns=str(cpd),trace=trace,scope='Same verified diagnostic floors/release mask; deterministic initial-only budget widening. No actual routes/nativeSTA or universal timing-offset guarantee.'),indent=2)+'\n');rows.append(dict(width=w,index=i,status='NET_SLACK_VECTOR_CONSTRUCTED',sha256=sha(file),nets=len(groups),raised_connections=sum(budget[k]>initial[k] for k in budget),preparation_seconds=time.perf_counter()-start));print(rows[-1],flush=True)
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
