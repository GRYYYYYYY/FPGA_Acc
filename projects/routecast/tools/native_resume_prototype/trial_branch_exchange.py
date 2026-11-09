"""Candidate-own worst-path NETs; freeze other NET ownership and query all released sinks."""
import json,re,struct,subprocess,sys,time,heapq
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:3]);penalty_ns=Fraction(sys.argv[3]);order=sys.argv[4];assert order in ('cid','delay');base=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07';out=ROOT/f'experiments/native_resume_branch_exchange_{order}_{sys.argv[3]}_w{w}_m{i}_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter()
verified=ROOT/'experiments/native_resume_singlepass_floor_controls_2026-10-07/verification.json';proof=json.loads(verified.read_text());assert all(sha(f)==h for f,h in proof['bindings'].items());route=base/'canonical/design.route';report=base/'canonical/report_timing.setup.rpt';body=report.read_text().split('#Path 2')[0];paths=physical_paths(route);selected=[]
for atom,port in re.findall(r'^(\S+)\.(inpad|out)\[\d+\]\s+\(',body,re.M):
 if atom in paths and paths[atom] and atom not in selected:selected.append(atom)
assert selected
endpoint=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(endpoint.read_text());graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);names=meta['net_names'];owners={name:{n for p in ps for n,sw in p} for name,ps in paths.items() if ps};occupancy=Counter(n for union in owners.values() for n in union);assert all(v<=f['capacities'][n] for n,v in occupancy.items());prepared=time.perf_counter()
binary=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor';prior=base/'floor_context/epoch_1/receipt.json';unconditional={x['query']['connection_id']:x['minimum_integer'] for x in json.loads(prior.read_text())['answers']};slot_by_arc={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};initial=[rc.initial(n) for n in range(len(nodes))]
span={}
for event,n in ET.iterparse(graph,events=('end',)):
 if n.tag=='node':
  if n.get('type') in ('CHANX','CHANY'):
   loc=n.find('loc');span[int(n.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
  n.clear()
penalty=penalty_ns*rc.scale/10**9;assert penalty.denominator==1;penalty=int(penalty)
weights=[d+penalty*span.get(f['dest_ranks'][slot],0) for slot,d in enumerate(rc.increments)];assert max(initial)+len(nodes)*max(weights)<2**64
protocol=dict(order=order,penalty_ns=str(penalty_ns),inputs={str(p):sha(p) for p in (verified,route,report,endpoint,graph,binary,prior,Path(__file__))},selected_net_names=selected,policy='All external NET drivers appearing on own final worst setup path; all sinks per selected NET. Freeze all other NET node-union ownership; release whole selected NET. Graph-model additive RC only, no cold labels; final candidate acquisition/proof cost excluded.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for index,name in enumerate(selected):
 qs=[q for q in queries if names[str(q['net_id'])]==name];assert qs
 other={n:count-int(n in owners[name]) for n,count in occupancy.items()};capacity=[max(0,f['capacities'][n]-other.get(n,0)) for n in range(len(nodes))];assert all(capacity[q['source']]>0 and capacity[q['sink']]>0 for q in qs)
 current_by_cid={};current_edges={}
 for q in qs:
  cp=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(cp)==1
  ee=[f['edge_ids'][slot_by_arc[u,v,sw]] for (u,_),(v,sw) in zip(cp[0],cp[0][1:])]
  current_edges[q['connection_id']]=ee;current_by_cid[q['connection_id']]=rc.path(q['source'],q['sink'],ee)
 qs=sorted(qs,key=lambda q: (-current_by_cid[q['connection_id']],q['connection_id']) if order=='delay' else (q['connection_id'],))
 assert len({q['source'] for q in qs})==1
 source=qs[0]['source'];current_slots={cid:[slot_by_arc[u,v,sw] for (u,_),(v,sw) in zip(cp,cp[1:])] for cid,cp in ((q['connection_id'],[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']][0]) for q in qs)};records=[];conflicts=[];attempts=[]
 def state(ps):
  union={source};parents={};delays={source:initial[source]}
  for slots in ps.values():
   u=source;delay=initial[source]
   for slot in slots:
    v=f['dest_ranks'][slot];delay+=rc.increments[slot]
    assert v not in parents or parents[v]==(u,slot)
    assert v not in delays or delays[v]==delay
    parents[v]=(u,slot);delays[v]=delay;union.add(v);u=v
  return union,parents,delays
 original_budget=sum(span.get(n,0) for n in owners[name])
 for q in qs:
  cid=q['connection_id'];sink=q['sink'];old_delay=sum(rc.increments[slot] for slot in current_slots[cid])+initial[source]
  retained={k:v for k,v in current_slots.items() if k!=cid};tree,tree_parent,tree_delay=state(retained)
  dist={n:tree_delay[n] for n in tree};pred={};heap=[(v,n) for n,v in dist.items()];heapq.heapify(heap)
  while heap:
   cost,u=heapq.heappop(heap)
   if dist[u]!=cost:continue
   if u==sink:break
   for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
    v=f['dest_ranks'][slot]
    if not capacity[v] or v in tree:continue
    trial=cost+rc.increments[slot]+penalty*span.get(v,0)
    if trial<dist.get(v,2**64):dist[v]=trial;pred[v]=(u,slot);heapq.heappush(heap,(trial,v))
  assert sink in dist
  suffix=[];u=sink
  while u not in tree:
   parent,slot=pred[u];suffix.append(slot);u=parent
  prefix=[]
  while u!=source:
   parent,slot=tree_parent[u];prefix.append(slot);u=parent
  slots=list(reversed(prefix))+list(reversed(suffix));trial_delay=initial[source]+sum(rc.increments[slot] for slot in slots);trial_paths=dict(retained);trial_paths[cid]=slots;trial_union,_,_=state(trial_paths);trial_wire=sum(span.get(n,0) for n in trial_union)
  accept=trial_delay<old_delay and trial_wire<=original_budget
  attempts.append(dict(connection_id=cid,old_delay=old_delay,trial_delay=trial_delay,trial_wire=trial_wire,accepted=accept))
  if accept:current_slots=trial_paths
 tree,tree_parent,tree_delay=state(current_slots)
 # Reconstruct after all sinks to prove shared parents and prefix delays.
 for q in qs:
  slots=[];u=q['sink']
  while u!=source:
   parent,slot=tree_parent[u];slots.append(slot);u=parent
  slots.reverse();edges=[f['edge_ids'][slot] for slot in slots];delay=rc.path(source,q['sink'],edges);assert delay==tree_delay[q['sink']] and delay>=unconditional[q['connection_id']]
  records.append(dict(query=q,unconditional_integer=unconditional[q['connection_id']],conditional_integer=delay,current_path_additive_integer=current_by_cid[q['connection_id']],physical_edge_ids=edges,changed_path=edges!=current_edges[q['connection_id']]))
 newunion=tree
 assert not conflicts and all(other.get(n,0)+1<=f['capacities'][n] for n in newunion)
 old_wire=sum(span.get(n,0) for n in owners[name]);new_wire=sum(span.get(n,0) for n in newunion)
 rows.append(dict(attempts=attempts,old_wire=old_wire,new_wire=new_wire,wire_budget_pass=new_wire<=old_wire,all_path_delays_no_worse=all(r['conditional_integer']<=r['current_path_additive_integer'] for r in records),net=name,records=records,other_occupancy={str(n):v for n,v in other.items() if v},new_union=sorted(newunion),consistent_parent_tree=True,other_net_capacity_feasible_union=True,conditional_floor_raised_connections=sum(x['conditional_integer']>x['unconditional_integer'] for x in records),positive_current_gap_connections=sum(x['current_path_additive_integer']>x['conditional_integer'] for x in records)));print(w,name,len(records),'raised',rows[-1]['conditional_floor_raised_connections'],'positive gaps',rows[-1]['positive_current_gap_connections'],'wire',old_wire,new_wire,'delay_no_worse',rows[-1]['all_path_delays_no_worse'],flush=True)
assert all(sha(p)==h for p,h in protocol['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),scale=rc.scale,preparation_seconds=prepared-start,query_and_proof_seconds=time.perf_counter()-prepared,total_seconds=time.perf_counter()-start,rows=rows,scope='Preserve other sink paths; replace one branch using multisource attachment. Commit only strict additive delay improvement and wholeNET union within original budget. Fixed sink order and penalty; not exact constrained optimization. Whole released NET independent shortest paths share a predecessor tree and respect frozen otherNET node capacities. Not native pin/configurability/timing validation, not shared-tree loaded STA or simultaneous replacement of multiple NETs. Selection retrospective own final candidate, no cold oracle.'),indent=2)+'\n')
