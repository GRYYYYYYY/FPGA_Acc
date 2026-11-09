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
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_wire_repair_2026-10-07';out.mkdir(exist_ok=False)
pf=ROOT/'experiments/mux32_critical_repair_2026-10-07/candidate.json';gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w32.json';af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml'
sources=closure([Path(__file__)]);inputs={str(p):sha(p) for p in (pf,gf,mf,af,graph)}
protocol=dict(sources=sources,inputs=inputs,max_attempts=32,max_labels=10000,policy='Order affected connections by exclusive channel span descending, then ID; try first32. Pareto marginal union-wire vs exact RC labels, cap10000, RC <= current connection delay; fixed remaining sameNET parents, otherNET capacity. Accept only strict whole-candidate wire reduction with nonincreasing full model CPD',scope='Development on previously observed w32/m2, not heldout. Private candidate only; final native proof required. Preparation and search wall time included, independent verifier outside clock.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter()
c=copy.deepcopy(json.loads(pf.read_text()));records={str(q['connection_id']):q for q in c['records']};g=json.loads(gf.read_text());m=json.loads(mf.read_text());meta=json.loads(af.read_text());a=ImmutableXMLAudit(graph,c['graph_sha256']);ids,classes,switches,_=read(graph);adj=[[] for _ in a.caps];weights={}
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

def wire(unions):
 return sum(a.spans[n] for used in unions.values() for n in used if a.types[n] in (4,5))

def constrained(q,rows):
 # Remaining same-NET tree is fixed; costs count new NET-union channel nodes.
 net=q['net_id'];rest=set();fixed={}
 for cid,record in rows.items():
  if record['net_id']!=net or cid==str(q['connection_id']):continue
  rest.add(record['source'])
  for eid in record['answer']['physical_edge_ids']:
   e=a.graph.edges[eid];rest.update((e.source,e.sink));fixed[e.sink]=(e.source,eid)
 unions,ledger,_,_,_,_=state(rows);other={n:v-int(n in unions[net]) for n,v in ledger.items()}
 allowed=lambda n:a.caps[n]>0 and other.get(n,0)<a.caps[n]
 src,sink=q['source'],q['sink'];res,cap=classes[ids[src]];initial=res*cap/2;budget=F(q['answer']['delay'],c['scale'])
 labels=[(src,initial,0,None,None)];front=defaultdict(list);front[src]=[0];heap=[(0,initial,0)];expanded=0
 while heap:
  cost,delay,lid=heapq.heappop(heap);node=labels[lid][0]
  if lid not in front[node]:continue
  expanded+=1
  if node==sink:
   edges=[]
   while labels[lid][3] is not None:
    edges.append(labels[lid][4]);lid=labels[lid][3]
   return dict(status='FOUND',delay=delay,edges=list(reversed(edges)),labels=len(labels),expanded=expanded)
  for dst,eid,inc in adj[node]:
   if not allowed(dst) or (dst in fixed and fixed[dst]!=(node,eid)):continue
   nd=delay+inc
   if nd>budget:continue
   nc=cost+(a.spans[dst] if dst not in rest and a.types[dst] in (4,5) else 0)
   if any(labels[k][1]<=nd and labels[k][2]<=nc for k in front[dst]):continue
   if len(labels)>=10000:return dict(status='LABEL_LIMIT',labels=len(labels),expanded=expanded)
   front[dst]=[k for k in front[dst] if not (nd<=labels[k][1] and nc<=labels[k][2])]
   nl=len(labels);labels.append((dst,nd,nc,lid,eid));front[dst].append(nl);heapq.heappush(heap,(nc,nd,nl))
 return dict(status='UNREACHABLE',labels=len(labels),expanded=expanded)

initial=state(records);initial_wire=wire(initial[0]);assert initial[4:]==(0,0)
# Deterministic exclusive channel contribution order; only affected connections.
def contribution(cid):
 q=records[cid];own=set();rest=set()
 for k,record in records.items():
  if record['net_id']!=q['net_id']:continue
  used={record['source']}
  for eid in record['answer']['physical_edge_ids']:
   e=a.graph.edges[eid];used.update((e.source,e.sink))
  (own if k==cid else rest).update(used)
 return sum(a.spans[n] for n in own-rest if a.types[n] in (4,5))
order=sorted(affected,key=lambda k:(-contribution(k),int(k)))[:32]
trace=[]
for cid in order:
 current=state(records);before_wire=wire(current[0]);answer=constrained(records[cid],records)
 event=dict(connection_id=cid,status=answer['status'],labels=answer['labels'],expanded=answer['expanded'],before_wirelength=before_wire,accepted=False)
 if answer['status']!='FOUND':trace.append(event);continue
 previous=records[cid];trial=copy.deepcopy(previous);trial['answer']['physical_edge_ids']=answer['edges'];encoded=answer['delay']*c['scale'];assert encoded.denominator==1;trial['answer']['delay']=int(encoded);trial['answer'].pop('cost',None);trial['mode']='WIRE_CONSTRAINED_RC_REPAIR';records[cid]=trial
 try:ns=state(records)
 except AssertionError:
  records[cid]=previous;event['reason']='INVALID_PATH';trace.append(event);continue
 after=wire(ns[0]);event.update(after_wirelength=after,parent_conflicts=ns[4],overflow_units=ns[5],model_cpd_ns=str(ns[3].cpd))
 if ns[4] or ns[5] or ns[3].cpd>initial[3].cpd or after>=before_wire:records[cid]=previous;event['reason']='NO_VALID_JOINT_IMPROVEMENT'
 else:event['accepted']=True
 trace.append(event)
final=state(records);c['records']=[records[k] for k in sorted(records,key=int)];c['ledger']=dict(final[1]);c['wire_repair_trace']=trace
(out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
assert all(sha(p)==h for p,h in {**sources,**inputs}.items())
receipt=dict(protocol_sha256=sha(out/'protocol.json'),candidate_sha256=sha(out/'candidate.json'),initial_cpd_ns=str(initial[3].cpd),final_cpd_ns=str(final[3].cpd),target_cpd_ns=str(target),initial_wirelength=initial_wire,final_wirelength=wire(final[0]),published_wirelength=11883,parent_conflicts=final[4],overflow_units=final[5],accepted_repairs=sum(x['accepted'] for x in trace),attempts=len(trace),producer_seconds=time.perf_counter()-start,trace=trace,scope=protocol['scope'])
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
