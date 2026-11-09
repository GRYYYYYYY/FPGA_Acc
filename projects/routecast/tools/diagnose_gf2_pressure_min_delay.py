"""Exact originalXML minimum delay with capacity-prefix restrictions; Bellman certificate."""
import json,heapq,time
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_pressure_frontier_repair_2026-10-06';r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/gf2_pressure_min_delay_2026-10-06';out.mkdir();cases=[]
for row in r['rows']:
 w=row['data_width'];ch=row['channels'];prior=base/f'gf2_d{w}_w{ch}/receipt.json';ep=root/f'experiments/gf2_pressure_prediction_2026-10-06/gf2_d{w}_w{ch}/endpoints.json';cases.append({'data_width':w,'channels':ch,'receipt':str(prior),'endpoints':str(ep),'bindings':{str(p):sha(p) for p in (prior,ep)}})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'source_sha256':sha(Path(__file__)),'scope':'Posthoc diagnostic only, no predictor rerun/tuning. OriginalXML exact Fraction bufferedRC Dijkstra to exhaustion after filtering otherNET saturated resources, independent Bellman inequalities and tight reachable predecessor chains. Graph-only minimum ignores singleNET tree-parent constraints; lower bound for constrained completion, not native STA.'},indent=2)+'\n');rows=[]
for c in cases:
 begin=time.monotonic();q=json.loads(Path(c['receipt']).read_text());ep=json.loads(Path(c['endpoints']).read_text());f=q['failure']['query'];graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph);unions=defaultdict(set)
 for rec in q['records']:
  net=rec['net_id'];unions[net].add(rec['source'])
  for eid in rec['answer']['physical_edge_ids']:unions[net].add(xml.graph.edges[eid].sink)
 ledger={int(n):v for n,v in q['ledger'].items()};other={n:v-int(n in unions[f['net_id']]) for n,v in ledger.items()};allowed={n for n in range(len(xml.caps)) if other.get(n,0)<xml.caps[n]};adj=defaultdict(list)
 for eid in range(len(xml.graph.edges)):
  e=xml.graph.edges[eid]
  if e.source in allowed and e.sink in allowed:adj[e.source].append((e.sink,eid,arc_delay(classes,switches,ids[e.sink],e.switch_id)))
 source=f['source'];sink=f['sink'];res,cap=classes[ids[source]];initial=res*cap/2;dist={source:initial} if source in allowed else {};back={};heap=[(initial,source)] if dist else []
 while heap:
  delay,node=heapq.heappop(heap)
  if delay!=dist[node]:continue
  for dst,eid,inc in adj[node]:
   assert inc>=0;nextdelay=delay+inc
   if dst not in dist or nextdelay<dist[dst]:dist[dst]=nextdelay;back[dst]=(node,eid);heapq.heappush(heap,(nextdelay,dst))
 # All finite labels are realized by tight predecessors. All admissible edges
 # satisfy Bellman inequalities, so no missed cheaper path or reachable node.
 for n,value in dist.items():
  if n!=source:
   prev,eid=back[n];e=xml.graph.edges[eid];assert e.source==prev and e.sink==n and dist[prev]+arc_delay(classes,switches,ids[n],e.switch_id)==value
  for dst,eid,inc in adj[n]:assert dst in dist and dist[dst]<=value+inc
 path=[];node=sink
 if sink in dist:
  seen={sink}
  while node!=source:
   node,eid=back[node];assert node not in seen;seen.add(node);path.append(eid)
  path.reverse()
 label='CAPACITY_DISCONNECTED' if sink not in dist else 'MIN_DELAY_OVER_1NS' if dist[sink]>Fraction(1,10**9) else 'WITHIN_BUDGET_GRAPH_PATH_EXISTS'
 witness={'query':f,'graph_sha256':ep['graph_sha256'],'allowed_nodes':sorted(allowed),'distances':{str(n):str(d) for n,d in dist.items()},'predecessors':{str(n):list(v) for n,v in back.items()},'physical_edge_ids':path};file=out/f"gf2_d{c['data_width']}_w{c['channels']}.json";file.write_text(json.dumps(witness,indent=2)+'\n');row={'data_width':c['data_width'],'channels':c['channels'],'failure':q['failure']['status'],'classification':label,'minimum_delay_ns':float(dist[sink]*10**9) if sink in dist else None,'reachable_nodes':len(dist),'certificate_sha256':sha(file),'diagnostic_s':time.monotonic()-begin};rows.append(row);assert all(sha(f)==h for f,h in c['bindings'].items());print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':True},indent=2)+'\n')
