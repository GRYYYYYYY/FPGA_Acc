"""Independent backward max-plus verification of capacity-adjusted vectors."""
import json
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_fullnet_capacity_budgets_2026-10-06';base=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';diag=ROOT/'experiments/mux_fullnet_forbidden_resource_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==12 and r['protocol_sha256']==sha(out/'protocol.json');rows=[]
for row in r['rows']:
 if row['status']=='ALLOCATION_NOT_SUBMITTED':continue
 w,i=row['width'],row['index'];file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];d=json.loads(file.read_text());af=base/f'w{w}_m{i}.json';df=diag/f'w{w}_m{i}.json';assert sha(af)==d['base_sha256'] and sha(df)==d['diagnostic_sha256'];a=json.loads(af.read_text());diagnostic=json.loads(df.read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mapping=json.loads(mf.read_text());incoming={int(n):[] for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 def evaluate(b):
  @lru_cache(None)
  def arrival(n):
   return max([F(0)]+[arrival(u)+(b[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
  return max(arrival(int(n)) for n,kind in tg['nodes'].items() if kind=='SINK')
 affected=set(map(str,a['affected']['affected_complete_net_connection_ids']));original={k:F(v) for k,v in a['floor_ns'].items()};target=F(a['target_cpd_ns']);options=[]
 for opt in d['options']:
  floor=dict(original);required={};supported=True
  for ans in diagnostic['answers']:
   if ans['query']['net_id']!=opt['net_id']:continue
   cid=str(ans['query']['connection_id'])
   if ans['minimum'] is None:supported=False;continue
   need=F(ans['minimum']*10**9,diagnostic['scale']);required[cid]=str(need)
   if cid not in affected and need>floor[cid]:supported=False
   floor[cid]=max(floor[cid],need)
  value=evaluate(floor);assert required==opt['required_ns'] and value==F(opt['model_floor_cpd_ns']);feasible=supported and value<=target and all(floor[cid]<=1 for cid in affected);assert feasible==opt['feasible'];options.append((value,opt['net_id'],floor,feasible))
 feasible=[x for x in options if x[3]]
 if not feasible:assert d['status']=='NO_CAPACITY_VECTOR_FROM_OPTIONS';continue
 chosen=min(feasible,key=lambda x:(x[0],x[1]));assert d['selected_net']==chosen[1];floor={k:F(v) for k,v in d['floor_ns'].items()};assert floor==chosen[2];budget={k:F(v) for k,v in d['budgets_ns'].items()};alpha=F(d['interpolation']);assert set(budget)==set(floor) and 0<=alpha<=1
 for cid,value in budget.items():assert value==(floor[cid]+alpha*(1-floor[cid]) if cid in affected else floor[cid])
 cpd=evaluate(budget);assert cpd==F(d['model_budget_cpd_ns']) and cpd<=target
 rows.append(dict(width=w,index=i,selected_net=d['selected_net'],model_cpd_ns=str(cpd),nodes=len(tg['nodes'])))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Exact rational backward full-fanin recurrence, option floors/selection and allocation constraints. No physical capacity realization or native STA guarantee.'),indent=2)+'\n');print(rows)
