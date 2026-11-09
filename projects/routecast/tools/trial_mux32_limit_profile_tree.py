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
from exact_connection_budget import connection_cap
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_limit_profile_tree_2026-10-07';out.mkdir(exist_ok=False)
pf=ROOT/'experiments/mux32_id_revisit_tree_2026-10-07/candidate.json';gf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w32_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w32.json';af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w32_m2.json';graph=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/rr_graph.xml'
selector=ROOT/'experiments/mux32_id_revisit_tree_2026-10-07/receipt.json';selected_nets={x['net_id'] for x in json.loads(selector.read_text())['trace'] if x.get('reason')=='LABEL_LIMIT'}
sources=closure([Path(__file__)]);inputs={str(p):sha(p) for p in (pf,gf,mf,af,graph,selector)}
protocol=dict(sources=sources,inputs=inputs,max_net_attempts=9,max_labels=20000,budget_rule='exact fixed-other-delay DAG cap, recalculated per connection; no sink dependency retains current RC as resource bound',policy='Use one private timing DAG per NET, exact sparse committed trial-delay updates; discard it on NET rejection. Full path/tree/RC/capacity checks at NET completion. Retry only previously label-limited affected NETs by union-wire descending/id. Release wholeNET, route connections ascending ID sharing new tree. Marginal union-wire exact RC Pareto search, cap20000labels, delay <= sequential exact DAG cap. Accept only full model CPD<=old target and strict complete union-wire decrease; reject restores all NET records',scope='Development on previously observed w32/m2, not heldout. Private candidate only; final native proof required. Preparation and search wall time included, independent verifier outside clock.')
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

def constrained(q,rows,budget):
 # Remaining same-NET tree is fixed; costs count new NET-union channel nodes.
 net=q['net_id'];rest=set();fixed={}
 for cid,record in rows.items():
  if record['net_id']!=net or cid==str(q['connection_id']):continue
  rest.add(record['source'])
  for eid in record['answer']['physical_edge_ids']:
   e=a.graph.edges[eid];rest.update((e.source,e.sink));fixed[e.sink]=(e.source,eid)
 unions=defaultdict(set)
 for record in rows.values():
  used=unions[record['net_id']];used.add(record['source'])
  for eid in record['answer']['physical_edge_ids']:
   e=a.graph.edges[eid];used.update((e.source,e.sink))
 ledger=Counter(n for used in unions.values() for n in used)
 other={n:v-int(n in unions[net]) for n,v in ledger.items()}
 allowed=lambda n:a.caps[n]>0 and other.get(n,0)<a.caps[n]
 src,sink=q['source'],q['sink'];res,cap=classes[ids[src]];initial=res*cap/2
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
   if len(labels)>=20000:return dict(status='LABEL_LIMIT',labels=len(labels),expanded=expanded)
   front[dst]=[k for k in front[dst] if not (nd<=labels[k][1] and nc<=labels[k][2])]
   nl=len(labels);labels.append((dst,nd,nc,lid,eid));front[dst].append(nl);heapq.heappush(heap,(nc,nd,nl))
 return dict(status='UNREACHABLE',labels=len(labels),expanded=expanded)

initial=state(records);initial_wire=wire(initial[0]);assert initial[4:]==(0,0)
# Rebuild complete affected NETs ordered by current union-wire contribution.
nets=set(records[cid]['net_id'] for cid in affected)&selected_nets
order=sorted(nets,key=lambda net:(-sum(a.spans[n] for n in initial[0][net] if a.types[n] in (4,5)),net))
trace=[]
for net in order:
 previous=dict(records);current=state(records);before_wire=wire(current[0]);netrows=sorted((q for q in records.values() if q['net_id']==net),key=lambda q:q['connection_id'])
 records={cid:q for cid,q in records.items() if q['net_id']!=net};events=[];failure=None;budgetdag=current[3]
 for q in netrows:
  cap=connection_cap(budgetdag,q['connection_id'],target)
  if not cap['feasible']:failure='MODEL_CAP_INFEASIBLE';events.append(dict(connection_id=q['connection_id'],status=failure));break
  limit=cap['cap_ns'] if cap['cap_ns'] is not None else F(q['answer']['delay']*10**9,c['scale'])
  answer=constrained(q,records,limit/10**9);event=dict(connection_id=q['connection_id'],status=answer['status'],budget_ns=str(limit),labels=answer['labels'],expanded=answer['expanded']);events.append(event)
  if answer['status']!='FOUND':failure=answer['status'];break
  trial=copy.deepcopy(q);trial['answer']['physical_edge_ids']=answer['edges'];encoded=answer['delay']*c['scale'];assert encoded.denominator==1;trial['answer']['delay']=int(encoded);trial['answer'].pop('cost',None);trial['mode']='WHOLE_NET_WIRE_RC_REPAIR';records[str(q['connection_id'])]=trial;budgetdag.update({str(q['connection_id']):answer['delay']*10**9},commit=True)
 event=dict(net_id=net,before_wirelength=before_wire,events=events,accepted=False)
 if failure is not None:records=previous;event['reason']=failure;trace.append(event);continue
 try:ns=state(records)
 except AssertionError:
  records=previous;event['reason']='INVALID_PATH';trace.append(event);continue
 after=wire(ns[0]);event.update(after_wirelength=after,parent_conflicts=ns[4],overflow_units=ns[5],model_cpd_ns=str(ns[3].cpd))
 if ns[4] or ns[5] or ns[3].cpd>target or after>=before_wire:records=previous;event['reason']='NO_VALID_JOINT_IMPROVEMENT'
 else:event['accepted']=True
 trace.append(event)
final=state(records);c['records']=[records[k] for k in sorted(records,key=int)];c['ledger']=dict(final[1]);c['wire_repair_trace']=trace
(out/'candidate.json').write_text(json.dumps(c,indent=2)+'\n')
assert all(sha(p)==h for p,h in {**sources,**inputs}.items())
receipt=dict(protocol_sha256=sha(out/'protocol.json'),candidate_sha256=sha(out/'candidate.json'),initial_cpd_ns=str(initial[3].cpd),final_cpd_ns=str(final[3].cpd),target_cpd_ns=str(target),initial_wirelength=initial_wire,final_wirelength=wire(final[0]),published_wirelength=11883,parent_conflicts=final[4],overflow_units=final[5],accepted_repairs=sum(x['accepted'] for x in trace),attempts=len(trace),producer_seconds=time.perf_counter()-start,trace=trace,scope=protocol['scope'])
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt)
