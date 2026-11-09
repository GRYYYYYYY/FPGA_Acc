"""Independent XML/Fraction checks for the selected NET14 snapshot diagnosis."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context,arc_delay
from exact_rc_lattice_direct_pairs_v2 import exact_scale
O=R/'experiments/mmc_net14_frozen_schedule_diagnosis_v2_2026-10-12';C=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12/model';bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
r=load(O/'receipt.json');bindings.update(r['bindings']);assert all(sha(p)==h for p,h in bindings.items())
f=load(C/'round0.json');history=load(C/'receipt.json');ep=load(R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json');queries={q['connection_id']:q for q in ep['connections']};graph=Path(ep['inputs']['graph']['path']);bindings[str(graph)]=sha(graph)
xml,ids,classes,switches,digest=load_context(graph,ep['graph_sha256']);scale,_=exact_scale(ids,classes,switches,xml.graph.edges)
def own(recs):
 result=set()
 for x in recs:
  u=x['source'];result.add(u)
  for eid in x['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==u;u=e.sink;result.add(u)
  assert u==x['sink']
 return result
records=defaultdict(list)
for x in f['records']:records[x['net_id']].append(x)
owned={n:own(v) for n,v in records.items()};base=Counter(n for v in owned.values() for n in v);assert dict(base)=={int(k):v for k,v in f['ledger'].items()}
changed={n for n,c in base.items() if c>xml.graph.nodes[n].capacity};assert changed=={int(k) for k in history['rounds'][1]['changed_nodes']};assert not owned[14]&changed
from fractions import Fraction
from load_structural_node_base_v1 import load as load_base
from load_initial_connection_criticalities_v1 import load as load_crit
nodebase,bb=load_base(len(xml.graph.nodes),scale);bindings.update(bb)
critdir=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';crit=load_crit(critdir);cp=load(critdir/'verification.json');bindings.update(cp['bindings'])
prices={int(k):v for k,v in f['prices'].items()}
for k,v in history['rounds'][1]['changed_nodes'].items():prices[int(k)]=prices.get(int(k),0)+v
weight=scale//(20*10**9)
def contribution(recs):
 users={};rawtotal=Fraction(0)
 for x in recs:
  c=Fraction(crit[x['connection_id']]['criticality_numerator'],crit[x['connection_id']]['criticality_denominator']);rawtotal+=c*x['answer']['delay']
  for eid in x['answer']['physical_edge_ids']:
   v=xml.graph.edges[eid].sink;users[v]=max(users.get(v,Fraction(0)),c)
 parts={}
 for n,c in users.items():
  node=xml.graph.nodes[n];span=0
  # XML node locations and type are obtained from the raw XML parameters below.
  row=xml.graph.nodes[n]
  parts[n]=[c]
 return rawtotal,users
# Independently read only node metadata from original XML for cost decomposition.
import xml.etree.ElementTree as ET
metadata={}
for event,el in ET.iterparse(graph,events=('end',)):
 if el.tag=='node':
  n=int(el.get('id'));loc=el.find('loc');span=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1 if el.get('type') in {'CHANX','CHANY'} else 0;metadata[n]=span;el.clear()
 if el.tag=='rr_nodes':break
affected_file=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/model/receipt.json'
affected=set(load(affected_file)['rounds'][1]['affected_nets'])
ledger=base.copy();current=dict(owned);counts=Counter();rows=[]
def score(recs,oldnodes):
 raw,users=contribution(recs);total=raw
 for n,c in users.items():
  span=metadata[n];hist=prices.get(n,0)-span;assert hist>=0
  other=ledger[n]-int(n in oldnodes);assert other>=0
  pressure=max(0,other-xml.graph.nodes[n].capacity+1)
  total+=(1-c)*(nodebase[n]*(1+hist)*(1+pressure)+weight*span)
 return total
for index,event in enumerate(history['rounds'][1]['events']):
 net=event['net_id'];oldrecs=records[net];oldnodes=current[net]
 if net not in affected:
  counts['skipped_nets']+=1
  if event['status']=='COMMITTED':
   newrecs=event['records'];oldbyid={x['connection_id']:x for x in oldrecs}
   changedids=[x['connection_id'] for x in newrecs if x['answer']['physical_edge_ids']!=oldbyid[x['connection_id']]['answer']['physical_edge_ids']]
   if changedids:
    before=score(oldrecs,oldnodes);after=score(newrecs,oldnodes);delta=after-before
    relation='strict_improvement' if delta<0 else 'equal' if delta==0 else 'worse';counts[relation]+=1
    rows.append({'net_id':net,'event_index':index,'relation':relation,'new_minus_old':str(delta),'old_score':str(before),'new_score':str(after),'changed_connection_ids':changedids,'prospective_overflow_delta':event['prospective_overflow_delta']})
   else:counts['committed_unchanged_paths']+=1
  else:counts[event['status']]+=1
 if event['status']=='COMMITTED':
  newnodes=own(event['records'])
  for n in oldnodes-newnodes:
   ledger[n]-=1
   if ledger[n]==0:del ledger[n]
  for n in newnodes-oldnodes:ledger[n]+=1
  current[net]=newnodes;records[net]=event['records']
assert counts['skipped_nets']==35940 and len(rows)==3178
final=load(C/'round1.json');assert dict(ledger)=={int(k):v for k,v in final['ledger'].items()}
assert all(sha(p)==h for p,h in bindings.items())
out=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12/skipped_net_objective_census_v1.json';assert not out.exists()
out.write_text(json.dumps(dict(bindings=bindings,counts=dict(counts),changed_skipped_events=rows,all_round1_events_ledger_replayed_and_final_frame_equal=True,scope='Exact Fraction objectives for all 3178 path-changing skipped NET commits under reconstructed recorded pre-event snapshots. Audited original event trajectories reused; no new candidate feasibility/optimality proof. Snapshot evolution can cause differences; common-state replay required before attributing strict benefit to static schedule omission. No quality or speed claim.'),indent=2)+'\n')
print('PASS SKIPPED NET OBJECTIVE CENSUS',dict(counts),flush=True)
