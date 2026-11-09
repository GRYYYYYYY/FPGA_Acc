"""Independent recursive full-DAG and retained-release shortest certificates."""
import json
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_critical_release_cost_replay_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==len(p['cases'])==12;rows=[]
for case,row in zip(p['cases'],r['rows']):
 w,i=case['width'],case['index'];file=out/f'w{w}_m{i}.json';assert sha(file)==row['sha256'];d=json.loads(file.read_text());af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';assert sha(af)==d['base_sha256'];a=json.loads(af.read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==d['graph_sha256']==a['graph_sha256'] and sha(mf)==d['mapping_sha256']==a['mapping_sha256'];tg=json.loads(tgf.read_text());mapping=json.loads(mf.read_text());ep=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in ep['connections']};incoming={int(n):[] for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 def edge_delay(eid,b):return b[a['edge_connection_ids'][eid]]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9
 def evaluate(b):
  @lru_cache(None)
  def arrival(n):return max([F(0)]+[arrival(u)+edge_delay(eid,b) for u,eid in incoming[n]])
  return max(arrival(int(n)) for n,kind in tg['nodes'].items() if kind=='SINK')
 floor={int(cid):F(v) for cid,v in a['floor_ns'].items()};expanded=set(a['affected']['affected_complete_net_connection_ids']);ctx=None
 if d['certificates']:
  ctx=PersistentRCContext(case['target']);f=ctx.rc.fields;inc=ctx.rc.increments;source_of={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
  for key,cert in d['certificates'].items():
   source=int(key);dist={int(n):v for n,v in cert['distances'].items()};pred={int(n):s for n,s in cert['predecessor_slots'].items()};assert dist[source]==0 and set(pred)==set(dist)-{source}
   for u,value in dist.items():
    for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     v=f['dest_ranks'][slot]
     if f['capacities'][v]<=0:continue
     assert v in dist and dist[v]<=value+inc[slot]
   rooted={source}
   for n in pred:
    seen=set();trail=[]
    while n not in rooted:
     assert n not in seen;seen.add(n);trail.append(n);slot=pred[n];u=source_of[slot];assert f['dest_ranks'][slot]==n and dist[n]==dist[u]+inc[slot];n=u
    rooted.update(trail)
 for step in d['trace']:
  before=evaluate(floor);assert before==F(step['before_cpd_ns'])>F(d['target_cpd_ns']);path=step['selection_path'];assert path and sum(edge_delay(eid,floor) for eid in path)==before
  assert not incoming[tg['edges'][path[0]]['source']] and tg['nodes'][str(tg['edges'][path[-1]]['sink'])]=='SINK'
  for left,right in zip(path,path[1:]):assert tg['edges'][left]['sink']==tg['edges'][right]['source']
  contributions={}
  for eid in path:
   cid=a['edge_connection_ids'].get(eid)
   if cid is not None and cid not in expanded:net=queries[cid]['net_id'];contributions[net]=contributions.get(net,F(0))+floor[cid]
  assert {str(net):str(value) for net,value in contributions.items()}==step['contributions_ns'];assert step['net_id']==min(contributions,key=lambda n:(-contributions[n],n));minima={}
  for cid,q in queries.items():
   if q['net_id']==step['net_id']:minima[cid]=F(d['certificates'][str(q['source'])]['distances'][str(q['sink'])]*10**9,ctx.rc.scale)
  assert {str(cid):str(v) for cid,v in minima.items()}==step['minima_ns'];floor.update(minima);expanded.update(minima);assert evaluate(floor)==F(step['after_cpd_ns'])
 assert d['added_nets']==[step['net_id'] for step in d['trace']] and len(d['trace'])<=4;assert sorted(expanded)==d['expanded_connection_ids'] and floor=={int(cid):F(v) for cid,v in d['floor_ns'].items()};value=evaluate(floor);assert value==F(d['model_floor_cpd_ns']);valid=value<=F(d['target_cpd_ns']) and all(floor[cid]<=1 for cid in expanded);assert valid==(d['status']=='CRITICAL_RELEASE_VECTOR_CONSTRUCTED')
 if valid:
  alpha=F(d['interpolation']);budget={int(cid):F(v) for cid,v in d['budgets_ns'].items()};assert 0<=alpha<=1 and set(budget)==set(floor)
  for cid,b in budget.items():assert b==(floor[cid]+alpha*(1-floor[cid]) if cid in expanded else floor[cid])
  assert evaluate(budget)==F(d['model_budget_cpd_ns'])<=F(d['target_cpd_ns'])
 rows.append(dict(width=w,index=i,status=d['status'],added_nets=d['added_nets']));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent recursive DAG, critical path selection/contributions, wholeNET release and exact shortest certificates for newly released NETs, budget interpolation. Original affected floor inputs retain prior diagnostic scope; no joint capacity/nativeSTA guarantee.'),indent=2)+'\n')
