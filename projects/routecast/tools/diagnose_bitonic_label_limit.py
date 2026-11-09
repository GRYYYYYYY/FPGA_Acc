"""Exact original XML shortest-delay witness, no predictor rerun or cap tuning."""
import json,heapq,time
from collections import defaultdict,Counter
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/bitonic_owner_union_prediction_2026-10-07';file=parent/'n16.json';epfile=ROOT/'experiments/bitonic_physical_endpoints_2026-10-07/n16/endpoints.json';out=ROOT/'experiments/bitonic_label_limit_diagnosis_2026-10-07';r=json.loads(file.read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');assert r['failure']['status']=='LABEL_LIMIT';q=r['failure']['query'];ep=json.loads(epfile.read_text());assert all(sha(x['path'])==x['sha256'] for x in ep['inputs'].values());graph=Path(ep['inputs']['graph']['path']);out.mkdir();bindings={str(f):sha(f) for f in [Path(__file__),file,epfile,parent/'verification.json',ROOT/'tools/immutable_xml_prediction_audit.py',ROOT/'tools/buffered_rc_node_classes.py',graph]};protocol=dict(bindings=bindings,query=q,budget_seconds='1/1000000000',scope='Retrospective exact diagnostic on original capacity state. No nativequery rerun, higherlabelcap, changedorder or newacceptedcandidate. OriginalXML exactbufferedRC Dijkstra stops atsettledsink, delays including SOURCE initialRC. Residual positivecapacity and fixedotherNET demand. Witness only for failedconnection, no wholecohort/CPD guarantee.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();a=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);adj=[[] for _ in a.caps];weights={}
for eid in range(len(a.graph.edges)):
 e=a.graph.edges[eid];key=(ids[e.sink],e.switch_id)
 if key not in weights:weights[key]=arc_delay(classes,switches,*key)
 adj[e.source].append((e.sink,eid,weights[key]))
unions=defaultdict(set)
for record in r['records']:
 u=unions[record['net_id']];u.add(record['source'])
 for eid in record['answer']['physical_edge_ids']:
  e=a.graph.edges[eid];u.update((e.source,e.sink))
ledger=Counter(node for u in unions.values() for node in u);assert dict(ledger)=={int(k):value for k,value in r['ledger'].items()};assert sorted(unions[q['net_id']])==r['attempts'][-1]['wire_owner_union'];other={node:count-int(node in unions[q['net_id']]) for node,count in ledger.items()}
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
 return dict(reachable=True,delay_seconds=str(delay),within_original_1ns_budget=delay<=F(1,10**9),physical_edge_ids=edges,settled_nodes=settled)
relaxed=shortest(False);residual=shortest(True);assert all(sha(f)==h for f,h in bindings.items());summary=dict(protocol_sha256=sha(out/'protocol.json'),relaxed=relaxed,residual=residual,original_native_answer=r['attempts'][-1]['native_answer'],diagnostic_seconds=time.perf_counter()-start,classification='ORIGINAL_LABEL_BOUND_TRUNCATED_FEASIBLE_CONNECTION' if residual.get('within_original_1ns_budget') else 'NO_RESIDUAL_BUDGET_WITNESS',scope=protocol['scope']);(out/'diagnosis.json').write_text(json.dumps(summary,indent=2)+'\n');print({k:value for k,value in summary.items() if k not in ('relaxed','residual')});print('relaxed',relaxed.get('delay_seconds'),'residual',residual.get('delay_seconds'))
