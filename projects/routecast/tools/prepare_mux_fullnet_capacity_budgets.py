"""Retrospective single-resource slack redistribution on the fixed full DAG."""
import json
from fractions import Fraction as F
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';diag=ROOT/'experiments/mux_fullnet_forbidden_resource_2026-10-06';out=ROOT/'experiments/mux_fullnet_capacity_budgets_2026-10-06';out.mkdir();p=json.loads((base/'protocol.json').read_text());rows=[]
(out/'protocol.json').write_text(json.dumps(dict(cases=p['cases'],base_receipt_sha256=sha(base/'receipt.json'),diagnostic_verification_sha256=sha(diag/'verification.json'),source_sha256=sha(Path(__file__)),policy='All12 cases. Retrospective diagnostic chosen resource. For each represented NET, lift its diagnosed avoidance connections to certified minimum, reset others to saved floors, then test full old timing DAG and cap. Select feasible option with lowest floor CPD, NET ID tie; 24-step uniform interpolation. No forbidden resource enforced during future reroute yet; no online policy or native STA guarantee.'),indent=2)+'\n')
for case in p['cases']:
 w,i=case['width'],case['index'];af=base/f'w{w}_m{i}.json';a=json.loads(af.read_text())
 if a['status']!='ALLFANIN_VECTOR_CONSTRUCTED':rows.append(dict(width=w,index=i,status='ALLOCATION_NOT_SUBMITTED'));continue
 df=diag/f'w{w}_m{i}.json';d=json.loads(df.read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());m=json.loads(mf.read_text());adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 q=deque(n for n in ind if not ind[n]);order=[]
 while q:
  u=q.popleft();order.append(u)
  for v,eid in adj[u]:
   ind[v]-=1
   if not ind[v]:q.append(v)
 assert len(order)==len(ind)
 def evaluate(b):
  arrival={n:F(0) for n in order}
  for u in order:
   for v,eid in adj[u]:
    delay=b[str(a['edge_connection_ids'][eid])]+F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9
    arrival[v]=max(arrival[v],arrival[u]+delay)
  return max(arrival[int(n)] for n,kind in tg['nodes'].items() if kind=='SINK')
 floor={cid:F(x) for cid,x in a['floor_ns'].items()};affected=set(map(str,a['affected']['affected_complete_net_connection_ids']));target=F(a['target_cpd_ns']);options=[];vectors={}
 for net in sorted({x['query']['net_id'] for x in d['answers']}):
  b=dict(floor);required={};supported=True
  for x in d['answers']:
   if x['query']['net_id']!=net:continue
   cid=str(x['query']['connection_id'])
   if x['minimum'] is None:supported=False;continue
   needed=F(x['minimum']*10**9,d['scale']);required[cid]=str(needed)
   if cid not in affected and needed>b[cid]:supported=False
   b[cid]=max(b[cid],needed)
  value=evaluate(b);feasible=supported and value<=target and all(b[cid]<=1 for cid in affected)
  options.append(dict(net_id=net,required_ns=required,model_floor_cpd_ns=str(value),feasible=feasible));vectors[net]=b
 feasible=[x for x in options if x['feasible']];selected=min(feasible,key=lambda x:(F(x['model_floor_cpd_ns']),x['net_id'])) if feasible else None
 budget={};low=F(0)
 if selected:
  floor=vectors[selected['net_id']];high=F(1);budget=dict(floor)
  for _ in range(24):
   mid=(low+high)/2;trial={cid:(v+mid*(1-v) if cid in affected else v) for cid,v in floor.items()}
   if evaluate(trial)<=target:budget=trial;low=mid
   else:high=mid
 status='CAPACITY_VECTOR_CONSTRUCTED' if selected else 'NO_CAPACITY_VECTOR_FROM_OPTIONS';f=out/f'w{w}_m{i}.json';f.write_text(json.dumps(dict(status=status,base_sha256=sha(af),diagnostic_sha256=sha(df),options=options,selected_net=selected['net_id'] if selected else None,forbidden_rank=d['forbidden_rank'],floor_ns={cid:str(v) for cid,v in floor.items()},budgets_ns={cid:str(v) for cid,v in budget.items()},target_cpd_ns=str(target),model_budget_cpd_ns=str(evaluate(budget)) if budget else None,interpolation=str(low)),indent=2)+'\n');row=dict(width=w,index=i,status=status,selected_net=selected['net_id'] if selected else None,sha256=sha(f));rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
