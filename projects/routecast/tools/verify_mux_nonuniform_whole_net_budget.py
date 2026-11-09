"""Stored shortest certificates and independent forward full-DAG budget audit."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,deque
from nonzero_rc_endpoint_context import load_endpoints
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_quadratic_repair_detours_2026-10-06';file=out/'nonuniform_whole_net_probe.json';d=json.loads(file.read_text());result=ROOT/'experiments/mux_quadratic_history_online_loop_2026-10-06/w8_m1/result.json';assert d['result_sha256']==sha(result);data=json.loads(result.read_text());spec=data['allocations'][data['attempts'][0]['allocation_index']];p=json.loads((result.parent.parent/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(8,1));ctx=load_endpoints(case['target']);rc=ctx[4];f=rc.fields;source_of={s:u for u in range(len(ctx[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};a=json.loads((ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w8_m1.json').read_text());gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w8_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w8.json';assert sha(gf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(gf.read_text());mapping=json.loads(mf.read_text());adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
for eid,e in tg['edges'].items():
 if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
queue=deque(n for n,v in ind.items() if not v);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  ind[v]-=1
  if not ind[v]:queue.append(v)
assert len(order)==len(ind);labels=0
for row in d['rows']:
 distances={}
 for source,cert in row['certificates'].items():
  source=int(source);dist={int(k):v for k,v in cert['distances'].items()};pred={int(k):v for k,v in cert['predecessor_slots'].items()};assert dist[source]==0 and 4937 not in dist and set(pred)==set(dist)-{source}
  for u,value in dist.items():
   for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][s]
    if v!=4937 and f['capacities'][v]>0:assert v in dist and dist[v]<=value+rc.increments[s]
  rooted={source}
  for node in pred:
   trail=[];seen=set()
   while node not in rooted:
    assert node not in seen;seen.add(node);trail.append(node);s=pred[node];u=source_of[s];assert f['dest_ranks'][s]==node and dist[node]==dist[u]+rc.increments[s];node=u
   rooted.update(trail)
  labels+=len(dist);distances[source]=dist
 budget={k:F(v) for k,v in spec['budgets_ns'].items()};queries=[q for q in ctx[5] if q['net_id']==row['net']];assert {q['connection_id'] for q in queries}=={r['connection_id'] for r in row['connections']}
 for q in queries:
  minimum=distances[q['source']][q['sink']];cid=str(q['connection_id']);budget[cid]=max(budget[cid],F(minimum*10**9,rc.scale));assert budget[cid]<=1
 assert budget=={k:F(v) for k,v in row['budgets_ns'].items()};arrival={n:F(0) for n in order}
 for u in order:
  for v,eid in adj[u]:
   delay=budget[str(a['edge_connection_ids'][eid])]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9
   arrival[v]=max(arrival[v],arrival[u]+delay)
 cpd=max(arrival[int(n)] for n,kind in tg['nodes'].items() if kind=='SINK');assert cpd==F(row['model_cpd_ns'])<=F(a['target_cpd_ns']);assert row['supported'] and row['within_cap'] and row['within_model_target']
(out/'whole_net_probe_verification.json').write_text(json.dumps(dict(probe_sha256=sha(file),verifier_sha256=sha(Path(__file__)),labels=labels,nets=[r['net'] for r in d['rows']],scope='Archived shortest certificates checked without solver; exact wholeNET budget raises and unchanged others, independent forward fullDAG CPD/caps. Separate alternatives only, no route/nativeSTA acceptance.'),indent=2)+'\n');print('verified wholeNET probes',labels)
