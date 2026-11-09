"""Bounded development critical-path repair; no proposed cold label input."""
import json,time,heapq,copy
from fractions import Fraction as F
from collections import defaultdict,Counter
from pathlib import Path
from pre_route_endpoints import sha
from freeze_priority_family import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from exact_incremental_timing_dag import ExactTimingDAG
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_continuous_critical_2026-10-07';out.mkdir(exist_ok=False)
pf=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/w32_m2/result.json';gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w32.json';af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml'
sources=closure([Path(__file__)]);inputs={str(p):sha(p) for p in (pf,gf,mf,af,graph)}
protocol=dict(sources=sources,inputs=inputs,max_rounds=16,policy='Trace deterministic max-arrival critical path, try affected connections descending current delay/id. Release own NET for exact residual shortest RC, reject parent/capacity violations; accept only lexicographic decrease in (full model CPD,total connection delay). Stop at old model CPD or no accepted repair. No proposed cold/native label inputs.',scope='Development on previously observed w32/m2, not heldout. Private candidate only; final native proof required. Preparation and search wall time included, independent verifier outside clock.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter()
c=copy.deepcopy(json.loads(pf.read_text())['result']['candidate']);records={str(q['connection_id']):q for q in c['records']};g=json.loads(gf.read_text());m=json.loads(mf.read_text());meta=json.loads(af.read_text());a=ImmutableXMLAudit(graph,c['graph_sha256']);ids,classes,switches,_=read(graph);adj=[[] for _ in a.caps];weights={}
for eid in range(len(a.graph.edges)):
 e=a.graph.edges[eid];key=(ids[e.sink],e.switch_id)
 if key not in weights:weights[key]=arc_delay(classes,switches,*key)
 adj[e.source].append((e.sink,eid,weights[key]))
affected=set(map(str,c['affected']['affected_complete_net_connection_ids']))
old={str(cid):F(m['external_edges'][eid]['branch']['rr_delay_seconds'])*10**9 for eid,cid in meta['edge_connection_ids'].items()}
target=ExactTimingDAG.from_native_metadata(g,m,meta,old).cpd

def state(rows):
 unions=defaultdict(set);parents=defaultdict(dict);delays={};conflicts=0
 for cid,q in rows.items():
  net=q['net_id'];node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
  for eid in q['answer']['physical_edge_ids']:
   e=a.graph.edges[eid];assert e.source==node and e.sink not in used
   incoming=(node,eid)
   if e.sink in parents[net] and parents[net][e.sink]!=incoming:conflicts+=1
   parents[net][e.sink]=incoming;node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
  assert node==q['sink'] and delay==F(q['answer']['delay'],c['scale'])
  unions[net].update(used);delays[cid]=delay*10**9
 ledger=Counter(n for used in unions.values() for n in used)
 overflow=sum(max(0,count-a.caps[n]) for n,count in ledger.items())
 dag=ExactTimingDAG.from_native_metadata(g,m,meta,delays)
 return unions,ledger,delays,dag,conflicts,overflow

def shortest(q,unions,ledger):
 net=q['net_id'];other={n:v-int(n in unions[net]) for n,v in ledger.items()}
 allowed=lambda n:a.caps[n]>0 and other.get(n,0)<a.caps[n]
 src,sink=q['source'],q['sink'];res,cap=classes[ids[src]];initial=res*cap/2
 if not allowed(src):return None
 dist={src:initial};prev={};queue=[(initial,src)]
 while queue:
  value,node=heapq.heappop(queue)
  if dist[node]!=value:continue
  if node==sink:
   edges=[]
   while node!=src:node,eid=prev[node];edges.append(eid)
   return value,list(reversed(edges))
  for dst,eid,inc in adj[node]:
   if not allowed(dst):continue
   value2=value+inc
   if dst not in dist or value2<dist[dst]:dist[dst]=value2;prev[dst]=(node,eid);heapq.heappush(queue,(value2,dst))
 return None
trace=[];initial_state=state(records);assert initial_state[4:]==(0,0)
for iteration in range(16):
 unions,ledger,delays,dag,_,_=state(records)
 if dag.cpd<=target:break
 node=min(n for n in dag.sinks if dag.arrivals[n]==dag.cpd);critical=[]
 while dag.arrivals[node]>0:
  options=[x for x in dag.incoming[node] if dag.arrivals[x[0]]+x[1]+(delays[x[2]] if x[2] is not None else 0)==dag.arrivals[node]]
  u,offset,cid=min(options,key=lambda x:(x[0],str(x[2]),x[1]))
  if cid in affected:critical.append(cid)
  node=u
 accepted=False
 for cid in sorted(set(critical),key=lambda k:(-delays[k],int(k))):
  answer=shortest(records[cid],unions,ledger);event=dict(iteration=iteration,connection_id=cid,before_cpd_ns=str(dag.cpd),old_delay_ns=str(delays[cid]),accepted=False)
  if answer is None:event['reason']='RESIDUAL_DISCONNECTED';trace.append(event);continue
  value,edges=answer;event['new_delay_ns']=str(value*10**9)
  if value*10**9>=delays[cid]:event['reason']='NO_DELAY_IMPROVEMENT';trace.append(event);continue
  previous=records[cid];trial=copy.deepcopy(previous);trial['answer']['physical_edge_ids']=edges;encoded=value*c['scale'];assert encoded.denominator==1;trial['answer']['delay']=int(encoded);trial['answer'].pop('cost',None);trial['mode']='CRITICAL_EXACT_RC_REPAIR';records[cid]=trial
  ns=state(records);event.update(after_cpd_ns=str(ns[3].cpd),parent_conflicts=ns[4],overflow_units=ns[5])
  if ns[4] or ns[5] or (ns[3].cpd,sum(ns[2].values())) >= (dag.cpd,sum(delays.values())):
   records[cid]=previous;event['reason']='TOPOLOGY_CAPACITY_OR_MODEL_REJECT'
  else:event['accepted']=True;accepted=True
  trace.append(event)
  if accepted:break
 if not accepted:break
final=state(records);c['records']=[records[k] for k in sorted(records,key=int)];c['ledger']=dict(final[1]);c['critical_repair_trace']=trace
(out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
assert all(sha(p)==h for p,h in {**sources,**inputs}.items())
receipt=dict(protocol_sha256=sha(out/'protocol.json'),candidate_sha256=sha(out/'candidate.json'),initial_cpd_ns=str(initial_state[3].cpd),final_cpd_ns=str(final[3].cpd),target_cpd_ns=str(target),model_timing_pass=final[3].cpd<=target,parent_conflicts=final[4],overflow_units=final[5],accepted_repairs=sum(x['accepted'] for x in trace),attempts=len(trace),producer_seconds=time.perf_counter()-start,trace=trace,scope=protocol['scope'])
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
