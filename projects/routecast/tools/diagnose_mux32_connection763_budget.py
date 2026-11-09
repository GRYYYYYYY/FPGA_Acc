"""Exact original XML shortest-delay witness, no predictor rerun or cap tuning."""
import json,heapq,time
from collections import defaultdict,Counter
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor'
file=parent/'w32_m2/result.json'
original=json.loads(file.read_text());r=original['result']['candidate']
receipt=json.loads((parent/'receipt.json').read_text())
assert next(x for x in receipt['rows'] if (x['width'],x['index'])==(32,2))['result_sha256']==sha(file)
q=next(x for x in r['records'] if x['connection_id']==763)
graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml'
capfile=ROOT/'experiments/mux32_incremental_gap_2026-10-07/verification.json'
limit_ns=F(json.loads(capfile.read_text())['connection_763_necessary_cap_if_other_delays_fixed_ns'])
out=ROOT/'experiments/mux32_connection763_budget_2026-10-07';out.mkdir(exist_ok=False)
bindings={str(f):sha(f) for f in [Path(__file__),file,parent/'receipt.json',capfile,ROOT/'tools/immutable_xml_prediction_audit.py',ROOT/'tools/buffered_rc_node_classes.py',graph]}
protocol=dict(bindings=bindings,query=q,budget_seconds=str(limit_ns/10**9),scope='Retrospective DEVELOPMENT exact original XML buffered RC shortest delay. Release complete queried NET for residual search; other NET unions fixed. Single-path necessary timing cap only, no compatible complete NET tree or native quality/gain proof.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
start=time.perf_counter();a=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);adj=[[] for _ in a.caps];weights={}
for eid in range(len(a.graph.edges)):
 e=a.graph.edges[eid];key=(ids[e.sink],e.switch_id)
 if key not in weights:weights[key]=arc_delay(classes,switches,*key)
 adj[e.source].append((e.sink,eid,weights[key]))
unions=defaultdict(set)
for record in r['records']:
 u=unions[record['net_id']];u.add(record['source'])
 for eid in record['answer']['physical_edge_ids']:
  e=a.graph.edges[eid];u.update((e.source,e.sink))
ledger=Counter(node for u in unions.values() for node in u);assert dict(ledger)=={int(k):value for k,value in r['ledger'].items()};other={node:count-int(node in unions[q['net_id']]) for node,count in ledger.items()}
def shortest(residual):
 src,sink=q['source'],q['sink'];res,cap=classes[ids[src]];initial=res*cap/2;dist={};prev={};queue=[];settled=0
 def allowed(node):return a.caps[node]>0 and (not residual or other.get(node,0)<a.caps[node])
 if allowed(src):dist[src]=initial;queue=[(initial,src)]
 while queue:
  value,node=heapq.heappop(queue)
  if value!=dist[node]:continue
  settled+=1
  if node==sink:break
  for dst,eid,inc in adj[node]:
   if not allowed(dst):continue
   proposed=value+inc
   if dst not in dist or proposed<dist[dst]:dist[dst]=proposed;prev[dst]=(node,eid);heapq.heappush(queue,(proposed,dst))
 else:return dict(reachable=False,settled_nodes=settled)
 edges=[];node=sink
 while node!=src:node,eid=prev[node];edges.append(eid)
 edges.reverse();node=src;delay=initial;used={src}
 for eid in edges:
  e=a.graph.edges[eid];assert e.source==node and e.sink not in used and allowed(e.sink);node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
 assert node==sink and delay==dist[sink]
 return dict(reachable=True,delay_seconds=str(delay),within_required_budget=delay<=limit_ns/10**9,physical_edge_ids=edges,settled_nodes=settled)
relaxed=shortest(False);residual=shortest(True);assert all(sha(f)==h for f,h in bindings.items());summary=dict(protocol_sha256=sha(out/'protocol.json'),relaxed=relaxed,residual=residual,original_native_answer=q['answer'],diagnostic_seconds=time.perf_counter()-start,classification='RESIDUAL_PATH_WITHIN_NECESSARY_CAP' if residual.get('within_required_budget') else ('RESIDUAL_SHORTEST_DELAY_EXCEEDS_ORIGINAL_CAP' if residual.get('reachable') else 'RESIDUAL_DISCONNECTED'),scope=protocol['scope']);(out/'diagnosis.json').write_text(json.dumps(summary,indent=2)+'\n');print({k:value for k,value in summary.items() if k not in ('relaxed','residual')});print('relaxed',relaxed.get('delay_seconds'),'residual',residual.get('delay_seconds'))
