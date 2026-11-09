"""Post-admission original XML/Fraction actual old-tree objective comparison."""
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
D=R/'experiments/mmc_joint_frozen_candidates_full_sink_v3_2026-10-09'
M=R/'experiments/mmc_triangular_span_v9_2026-10-09/model'
A=R/'experiments/mmc_triangular_retained_attempt_replay_v1_2026-10-09'
bindings=closure([Path(__file__)])
def load(p):
 bindings[str(p)]=sha(p);return json.loads(p.read_text())
admission=load(D/'verification.json');assert admission['all_original_XML_Fraction_selected_trees_budget_parent_and_membership_checks_pass'] and admission['audited_selected_connection_occurrences']==80868
for p,h in admission['bindings'].items():assert sha(p)==h;bindings[p]=h
r=load(D/'receipt.json');assert r['all_original_retained_events_processed'] and r['events']==2192
assert r['all_unrestricted_small_NET_outputs_equal_v2'] and r['all_events_have_budget_safe_incumbent']
for p,h in r['bindings'].items():assert sha(p)==h;bindings[p]=h
protocol=load(D/'protocol.json');assert protocol['state_limit']==10000 and protocol['sink_recursion_guard'] is None
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

initial_frame=load(M/'initial.json');previous_frame=load(M/'round0.json')
old_frames=[{x['connection_id']:x for x in f['records']} for f in (initial_frame,previous_frame)]
model_receipt=load(M/'receipt.json')
events={(i,e['net_id']):e for i,rr in enumerate(model_receipt['rounds']) for e in rr['events'] if e['status']=='RETAIN_BUDGET_OR_UNREACHABLE'}
identity=load(R/'experiments/retained_old_tree_identity_v1_2026-10-09/receipt.json');assert identity['all_retained_events_preserve_exact_old_records_and_epoch']
for p,h in identity['bindings'].items():assert sha(p)==h;bindings[p]=h
counts=Counter();outcomes=[]
for row in selections:
 key=(row['round'],row['net_id']);event=events[key];a=attempts[key];qs=[queries[x['connection_id']] for x in a['attempts']];prices=states[row['round']]['prices']
 old={q['sink']:old_frames[row['round']][q['connection_id']]['answer']['physical_edge_ids'] for q in qs}
 epoch=1 if row['round']==0 else previous_frame['epochs'][str(row['net_id'])]
 assert epoch==event['old_epoch']==event['new_epoch']
 chosen={int(s):p for s,p in row['paths'].items()}
 old_cost=tree(qs,old,prices);new_cost=tree(qs,chosen,prices);assert new_cost==row['union_cost']
 counts['events']+=1;counts['changed_from_actual_old']+=chosen!=old
 reason='lower' if new_cost<old_cost else ('equal' if new_cost==old_cost else 'higher')
 counts[reason+'_actual_old_union_objective']+=1
 outcomes.append(dict(round=row['round'],net_id=row['net_id'],old_epoch=epoch,actual_old_union_cost=old_cost,candidate_union_cost=new_cost,delta=new_cost-old_cost,changed=chosen!=old,search_status=row['status']))
assert counts['events']==2192 and all(sha(p)==h for p,h in bindings.items())
f=D/'actual_old_comparison.json';f.write_text(json.dumps(outcomes)+'\n');bindings[str(f)]=sha(f)
result=dict(bindings=bindings,all_actual_old_epochs_paths_budgets_and_union_costs_checked=True,counts=dict(counts),scope='Descriptive frozen-price comparison against actual archived old tree. No model transaction, updated round prices, congestion/QoR/native/full workflow gain.')
(D/'actual_old_comparison_receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['counts'],indent=2),flush=True)
