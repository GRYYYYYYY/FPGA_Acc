"""Independent original XML/Fraction selected-tree and candidate membership audit.
Does not independently certify candidate-set optimization optimality.
"""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from exact_rc_lattice_unique_pairs_v1 import exact_scale
D=R/'experiments/mmc_joint_frozen_candidates_v1_2026-10-09'
M=R/'experiments/mmc_triangular_span_v9_2026-10-09/model'
A=R/'experiments/mmc_triangular_retained_attempt_replay_v1_2026-10-09'
bindings=closure([Path(__file__)])
def load(p):
 bindings[str(p)]=sha(p);return json.loads(p.read_text())
r=load(D/'receipt.json');assert r['all_original_retained_events_processed'] and r['events']==2192
for p,h in r['bindings'].items():assert sha(p)==h;bindings[p]=h
protocol=load(D/'protocol.json');assert protocol['state_limit']==10000 and protocol['sink_recursion_guard']==500
p=load(M.parent/'protocol.json');ep=load(Path(p['endpoint']));graph=Path(ep['inputs']['graph']['path'])
xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];scale,_=exact_scale(ids,classes,switches,xml.graph.edges)
weight=load(M/'protocol.json')['price_unit_integer'];assert weight==scale//(20*10**9)
witness={w['connection_id']:w for w in load(M/'initial.json')['records']}
queries={q['connection_id']:q for q in ep['connections']}
query_ids=defaultdict(set)
for cid,q in queries.items():query_ids[q['net_id']].add(cid)
states=[load(M/'round0.json'),load(M/'round1.json')]
attempts={(x['round'],x['net_id']):x for x in load(A/'attempts.json')}
selections=load(D/'selections.json');assert len(selections)==2192 and {(x['round'],x['net_id']) for x in selections}==set(attempts)
counts=Counter();path_count=0

def tree(qs,paths,prices):
 src=qs[0]['source'];assert all(q['source']==src for q in qs)
 rr,cc=classes[ids[src]];start=rr*cc/2;union=set();parents={}
 assert xml.graph.nodes[src].capacity>0
 for q in qs:
  w=witness[q['connection_id']];assert all(w[k]==q[k] for k in q)
  u=src;seen={u};delay=start
  for eid in paths[q['sink']]:
   assert type(eid) is int and 0<=eid<len(xml.graph.edges)
   e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen and xml.graph.nodes[e.sink].capacity>0
   assert e.sink not in parents or parents[e.sink]==(u,eid)
   parents[e.sink]=(u,eid);union.add(eid);seen.add(e.sink);u=e.sink
   delay+=arc_delay(classes,switches,ids[u],e.switch_id)
  assert u==q['sink'];raw=delay*scale;assert raw.denominator==1 and raw.numerator<=w['budget_integer']
  if paths[q['sink']]==w['answer']['physical_edge_ids']:assert raw.numerator==w['answer']['delay']
 cost=start*scale
 for eid in union:
  e=xml.graph.edges[eid];cost+=arc_delay(classes,switches,ids[e.sink],e.switch_id)*scale+weight*prices.get(str(e.sink),0)
 assert cost.denominator==1
 return cost.numerator

for row in selections:
 a=attempts[row['round'],row['net_id']];qs=[queries[x['connection_id']] for x in a['attempts']];prices=states[row['round']]['prices']
 assert len(qs)==len(query_ids[row['net_id']]) and {q['connection_id'] for q in qs}==query_ids[row['net_id']]
 old={q['sink']:witness[q['connection_id']]['answer']['physical_edge_ids'] for q in qs}
 old_cost=tree(qs,old,prices);assert old_cost==row['old_union_cost']
 status=row['status'];assert status in {'OPTIMAL_WITHIN_CANDIDATES','UNKNOWN_STATE_LIMIT','UNKNOWN_SINK_RECURSION_GUARD'}
 assert 0<=row['states']<=10000
 if status=='UNKNOWN_SINK_RECURSION_GUARD':assert len(old)>500 and row['states']==0
 else:assert len(old)<=500
 if status=='UNKNOWN_STATE_LIMIT':assert row['states']==10000
 chosen=row['paths']
 if chosen is None:assert status!='OPTIMAL_WITHIN_CANDIDATES' and row['union_cost'] is None
 else:
  chosen={int(s):p for s,p in chosen.items()};assert set(chosen)==set(old)
  for attempt,q in zip(a['attempts'],qs):
   assert chosen[q['sink']] in (old[q['sink']],attempt['physical_edge_ids'])
  cost=tree(qs,chosen,prices);assert cost==row['union_cost']
  if status=='OPTIMAL_WITHIN_CANDIDATES':assert cost<=old_cost
  counts['feasible_incumbent']+=1;counts['changed_from_initial']+=chosen!=old;counts['lower_union_objective_than_initial']+=cost<old_cost
  path_count+=len(qs)
 counts[status]+=1
assert dict(counts)==r['counts'],(counts,r['counts'])
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,all_original_XML_Fraction_selected_trees_budget_parent_and_membership_checks_pass=True,events=2192,audited_selected_connection_occurrences=path_count,counts=dict(counts),scope='Independent complete event coverage and selected-tree safety/membership/union objective reconstruction. Not independent optimization optimality proof, production state update, native quality or complete workflow time gain.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)
