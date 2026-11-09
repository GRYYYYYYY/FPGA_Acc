"""Independent XML/Fraction checks for the selected NET133 snapshot diagnosis."""
import sys,json
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from independent_fraction_arc_context_v2 import load_context,arc_delay
from exact_rc_lattice_direct_pairs_v2 import exact_scale
O=R/'experiments/mmc_net133_frozen_schedule_diagnosis_v1_2026-10-12';C=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12/model';bindings=closure([Path(__file__)])
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
changed={n for n,c in base.items() if c>xml.graph.nodes[n].capacity};assert changed=={int(k) for k in history['rounds'][1]['changed_nodes']};assert not owned[133]&changed
pre=dict(owned)
for e in history['rounds'][1]['events']:
 if e['net_id']==133:expected=e;break
 if e['status']=='COMMITTED':pre[e['net_id']]=own(e['records'])
preledger=Counter(n for v in pre.values() for n in v);summaries={}
for mode,ledger in [('common_round0',base),('recorded_pre_net133',preledger)]:
 event=r['results'][mode];assert event['status']=='COMMITTED';recs=event['records'];assert {x['connection_id'] for x in recs}=={x['connection_id'] for x in records[133]};parents={}
 for x in recs:
  q=queries[x['connection_id']];assert all(x[k]==q[k] for k in q);u=x['source'];seen={u};a,b=classes[ids[u]];delay=a*b/2
  for eid in x['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen;assert xml.graph.nodes[e.sink].capacity>0;v=e.sink;incoming=(u,eid);assert v not in parents or parents[v]==incoming;parents[v]=incoming;seen.add(v);delay+=arc_delay(classes,switches,ids[v],e.switch_id);u=v
  assert u==x['sink'] and delay*scale==x['answer']['delay'] and x['answer']['delay']<=x['budget_integer'];assert x['budget_integer']==max(scale//10**9,(3*x['floor_integer']+1)//2)
 new=own(recs);touched=new|owned[133];delta=sum(max(0,ledger[n]+int(n in new)-int(n in owned[133])-xml.graph.nodes[n].capacity)-max(0,ledger[n]-xml.graph.nodes[n].capacity) for n in touched);assert delta==event['prospective_overflow_delta'] and delta<=0
 summaries[mode]={'connections':len(recs),'overflow_delta':delta,'changed_connection_ids':[x['connection_id'] for x in recs if x['answer']['physical_edge_ids']!=next(y for y in records[133] if y['connection_id']==x['connection_id'])['answer']['physical_edge_ids']]}
assert r['results']['recorded_pre_net133']['records']==expected['records']
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
objective={}
for mode,ledger in [('common_round0',base),('recorded_pre_net133',preledger)]:
 values={}
 for label,recs in [('old',records[133]),('new',r['results'][mode]['records'])]:
  raw,users=contribution(recs);total=raw;parts={}
  for n,c in users.items():
   span=metadata[n];hist=prices.get(n,0)-span;assert hist>=0
   other=ledger[n]-int(n in owned[133]);pressure=max(0,other-xml.graph.nodes[n].capacity+1)
   cost=nodebase[n]*(1+hist)*(1+pressure)+weight*span;value=(1-c)*cost;total+=value
   parts[str(n)]={'criticality':str(c),'base':nodebase[n],'history':hist,'other_occupancy':other,'pressure':pressure,'span':span,'weighted_cost':str(value)}
  values[label]={'score':str(total),'raw_component':str(raw),'node_contributions':parts};values[label+'_fraction']=total
 delta=values.pop('new_fraction')-values.pop('old_fraction');values['new_minus_old']=str(delta);values['relation']='strict_improvement' if delta<0 else 'equal' if delta==0 else 'worse';objective[mode]=values
assert all(sha(p)==h for p,h in bindings.items())
(O/'objective_verification_v2.json').write_text(json.dumps(dict(bindings=bindings,selected_net133_xml_fraction_budget_parent_and_snapshot_ledger_pass=True,old_ownership_intersects_round1_overflow_nodes=False,recorded_pre_event_candidate_equal_recorded_event=True,both_snapshot_candidates_equal=(r['results']['common_round0']['records']==r['results']['recorded_pre_net133']['records']),summaries=summaries,objective_comparison=objective,scope='NET133 physical and snapshot diagnosis only; no independent search optimality, candidate-cost cause, all skipped NET generalization, native QoR or speed proof.'),indent=2)+'\n');print('PASS NET133 independent objective audit',flush=True)
