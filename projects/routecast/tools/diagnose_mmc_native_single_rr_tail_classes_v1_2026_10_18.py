"""All-six single-overuse checkpoints: physical XML adjacency and actual co-owners."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
A=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18'
tp=A/'guard_resource_type_diagnostic_v1.json';T=json.loads(tp.read_text());assert T['status']=='pass'
cp=A/'cohort_verification.json';C=json.loads(cp.read_text());assert C['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass']
bindings={**T['bindings'],str(tp):sha(tp),str(cp):sha(cp),**closure([Path(__file__)])};cache=Cache()
with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
selections=[];targets=set()
for row in T['rows']:
 selected={int(i):x['single_overused_RR_node'] for i,x in row['iterations'].items() if x['single_overused_RR_node'] is not None}
 targets.update(selected.values());selections.append(dict(case=row['case'],arm=row['arm'],iteration_RR=selected))
D=R/'experiments/mmc_native_single_rr_tail_classes_v1_2026-10-18';D.mkdir()
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,selections=selections,criterion='All iteration-end checkpoints with exactly one overused RR across all6admitted traces; empty selections retained.',scope='Retrospective original XML adjacency and trace co-owner diagnostic only. No trace edits, parameter selection or new native run.'),f,indent=2)
ep=json.loads((R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256']
kinds=[];meta={};reverse=defaultdict(list);stack=[]
for event,e in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  n=int(e.get('id'));assert n==len(kinds);kind=e.get('type');kinds.append(kind)
  if n in targets or kind in ['IPIN','SINK']:meta[n]=dict(kind=kind,capacity=int(e.get('capacity')),loc=dict(e.find('loc').attrib))
  stack[-2].remove(e);e.clear()
 elif e.tag=='edge' and parent=='rr_edges':
  src,dst=int(e.get('src_node')),int(e.get('sink_node'))
  if kinds[src]=='IPIN' and kinds[dst]=='SINK':reverse[dst].append((src,int(e.get('switch_id'))))
  stack[-2].remove(e);e.clear()
 if e.tag=='rr_edges':break
 stack.pop()
adjacent=defaultdict(list)
for sink,edges in reverse.items():
 for ipin,switch in edges:
  if ipin in targets:adjacent[ipin].append(dict(sink_RR=sink,switch_id=switch))
rows=[]
for sel in selections:
 case,arm=sel['case'],sel['arm'];wanted=sel['iteration_RR'];epfile=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';ep=json.loads(epfile.read_text());demand=Counter(q['sink'] for q in ep['connections']);net_demand=Counter((q['net_id'],q['sink']) for q in ep['connections']);bindings[str(epfile)]=sha(epfile)
 trace=R/'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18'/case/arm/'owner_trace.tsv'
 proof=A/case/(arm+'.json');v=json.loads(proof.read_text());assert v['bindings'][str(trace)]==sha(trace);bindings[str(proof)]=sha(proof);witnesses=[];active=None;owners=[];measured=None
 if wanted:
  for line in trace.open():
   tag=line.partition(' ')[0].rstrip()
   if tag=='CP':
    w=line.split();it=int(w[2]);active=(it,wanted[it]) if w[1]=='iteration_end_after_local_opins' and it in wanted else None;owners=[];measured=None
   elif tag=='T' and active:
    w=line.split();count=w[6:].count(str(active[1]))
    if count:owners.append(dict(net=int(w[1]),ignored=int(w[2]),multiplicity=count))
   elif tag=='V' and active:
    w=line.split();assert int(w[1])==active[1] and measured is None;measured=dict(native_occ=int(w[2]),capacity=int(w[3]))
   elif tag=='CE' and active:
    it,node=active;assert measured is not None and sum(x['multiplicity'] for x in owners)==measured['native_occ'];assert measured['capacity']==meta[node]['capacity'];classes=[]
    for edge in adjacent[node]:
     sink=edge['sink_RR'];members=sorted({ipin for ipin,_ in reverse[sink]})
     classes.append(dict(sink_RR=sink,switch_id=edge['switch_id'],sink_metadata=meta[sink],current_input_connection_demand=demand[sink],adjacent_IPIN_RR_count=len(members),adjacent_IPIN_RRs=members))
    for owner in owners:
     owner['net_name']=ep['net_names'].get(str(owner['net']))
     owner['input_queries_to_adjacent_SINKs']={str(x['sink_RR']):net_demand[(owner['net'],x['sink_RR'])] for x in classes}
    witnesses.append(dict(iteration=it,RR=node,RR_metadata=meta[node],**measured,co_owners=owners,direct_SINK_adjacency=classes));active=None
 assert len(witnesses)==len(wanted)
 sinks={x['sink_RR'] for w in witnesses for x in w['direct_SINK_adjacency']}
 rows.append(dict(case=case,arm=arm,selected_checkpoints=len(witnesses),distinct_single_RRs=len(set(wanted.values())),distinct_adjacent_SINK_RRs=sorted(sinks),witnesses=witnesses))
 print('SINGLE RR TAIL CLASS',case,arm,len(witnesses),len(set(wanted.values())),sorted(sinks),flush=True)
with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
with (D/'diagnosis.json').open('x') as f:json.dump(dict(status='pass',bindings={**bindings,str(D/'protocol.json'):sha(D/'protocol.json')},rows=rows,scope='All6traces and fixed single-overuse checkpoint criterion. Direct originalXML IPIN-to-SINK adjacency, coordinates and actual co-owner multiplicities; input query counts are demand annotations, not a proof that every pin alternative is reachable or meets RC budgets. No exclusive causal claim, native-policy change, forecast improvement or timing benefit.'),f,indent=2)
print('ALL6SINGLE RR TAIL CLASS DIAGNOSTICS COMPLETE',flush=True)
