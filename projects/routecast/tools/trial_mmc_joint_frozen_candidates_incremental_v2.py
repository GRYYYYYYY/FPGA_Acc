"""Full original RR candidate parity with admitted v1; same search limits, no model updates."""
import json,sys,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from exact_rc_lattice_unique_pairs_v1 import exact_scale
from budget_joint_candidates_incremental_v2 import select
from budget_NET_gate_reference_v1 import audit
D=R/'experiments/mmc_joint_frozen_candidates_incremental_v2_2026-10-09';assert not D.exists()
B=R/'experiments/mmc_joint_frozen_candidates_v1_2026-10-09'
M=R/'experiments/mmc_triangular_span_v9_2026-10-09/model'
A=R/'experiments/mmc_triangular_retained_attempt_replay_v1_2026-10-09'
bindings=closure([Path(__file__)])
def load(p):
 bindings[str(p)]=sha(p);return json.loads(p.read_text())
baseline_proof=load(B/'verification.json');assert baseline_proof['all_original_XML_Fraction_selected_trees_budget_parent_and_membership_checks_pass']
for file,h in baseline_proof['bindings'].items():assert sha(file)==h;bindings[file]=h
baseline_receipt=load(B/'receipt.json')
baseline_rows=load(B/'selections.json');assert len(baseline_rows)==2192
for row in baseline_rows:
 if row['paths'] is not None:row['paths']={int(s):path for s,path in row['paths'].items()}
baseline={(row['round'],row['net_id']):row for row in baseline_rows};assert len(baseline)==2192
v=load(A/'verification.json');assert v['all_original_XML_paths_Fraction_RC_budgets_and_weighted_witness_comparisons_pass']
for p,h in v['bindings'].items():assert sha(p)==h;bindings[p]=h
protocol=load(M.parent/'protocol.json');ep=load(Path(protocol['endpoint']))
initial=load(M/'initial.json');witness={w['connection_id']:w for w in initial['records']}
queries={q['connection_id']:q for q in ep['connections']}
rows=load(A/'attempts.json');assert len(rows)==2192
states=[load(M/'round0.json'),load(M/'round1.json')]
weight=load(M/'protocol.json')['price_unit_integer']
D.mkdir();(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,state_limit=10000,sink_recursion_guard=500,policy='Incremental v2 full output parity, authenticated v1 admitted first. Every original retained event. Candidate set per sink: authenticated initial witness and unchanged-search replay only. No new path search, no model transaction, no native labels. Union-edge objective initial RC once plus raw+50ps destination price. Limits UNKNOWN; no unrestricted optimum or gain claim.'),indent=2)+'\n')
start=time.perf_counter();graph=Path(ep['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==ep['graph_sha256'];scale,_=exact_scale(ids,classes,switches,xml.graph.edges);assert weight==scale//(20*10**9)
print('Original XML/electrical context loaded',flush=True)
results=[];counts=Counter()
for i,row in enumerate(rows):
 qs=[queries[a['connection_id']] for a in row['attempts']];src=qs[0]['source'];assert all(q['source']==src for q in qs)
 budgets={};old={};candidates={};adj={};cap={src:xml.graph.nodes[src].capacity};prices=states[row['round']]['prices']
 for a,q in zip(row['attempts'],qs):
  w=witness[q['connection_id']];s=q['sink'];b=w['budget_integer'];paths=[w['answer']['physical_edge_ids'],a['physical_edge_ids']]
  if s in budgets:assert budgets[s]==b and old[s]==paths[0]
  budgets[s]=b;old[s]=paths[0];candidates[s]=paths
  for path in paths:
   for eid in path:
    e=xml.graph.edges[eid];f=arc_delay(classes,switches,ids[e.sink],e.switch_id)*scale;assert f.denominator==1
    arc=(eid,e.sink,f.numerator,weight*prices.get(str(e.sink),0));arcs=adj.setdefault(e.source,{})
    assert eid not in arcs or arcs[eid]==arc;arcs[eid]=arc;cap[e.sink]=xml.graph.nodes[e.sink].capacity
 adj={u:list(arcs.values()) for u,arcs in adj.items()}
 rr,cc=classes[ids[src]];init=rr*cc/2*scale;assert init.denominator==1;init=init.numerator
 old_audit=audit(adj,src,budgets,old,init,cap)
 edge_cost={(u,e):r+p for u,arcs in adj.items() for e,v,r,p in arcs}
 old_cost=init+sum(edge_cost[p] for p in old_audit['parents'].values())
 if len(budgets)>500:answer=dict(status='UNKNOWN_SINK_RECURSION_GUARD',paths=None,union_cost=None,states=0)
 else:answer=select(adj,src,budgets,candidates,init,cap,max_states=10000)
 assert dict(round=row['round'],net_id=row['net_id'],old_union_cost=old_cost,**answer)==baseline[row['round'],row['net_id']],(row['round'],row['net_id'])
 if answer['paths'] is not None:
  check=audit(adj,src,budgets,answer['paths'],init,cap)
  assert answer['union_cost']==init+sum(edge_cost[p] for p in check['parents'].values())
  if answer['status']=='OPTIMAL_WITHIN_CANDIDATES':assert answer['union_cost']<=old_cost
  counts['feasible_incumbent']+=1
  counts['changed_from_initial']+=answer['paths']!=old
  counts['lower_union_objective_than_initial']+=answer['union_cost']<old_cost
 assert answer['status']!='NO_COMPATIBLE_CANDIDATE_COMBINATION'
 counts[answer['status']]+=1
 results.append(dict(round=row['round'],net_id=row['net_id'],old_union_cost=old_cost,**answer))
 if (i+1)%100==0:print('Processed',i+1,dict(counts),flush=True)
assert len(results)==2192 and counts==baseline_receipt['counts'] and all(sha(p)==h for p,h in bindings.items())
f=D/'selections.json';f.write_text(json.dumps(results)+'\n');bindings[str(f)]=sha(f)
r=dict(bindings=bindings,all_original_retained_events_processed=True,all_v1_v2_complete_selection_outputs_identical=True,events=len(results),counts=dict(counts),diagnostic_seconds=time.perf_counter()-start,scope='Full original-graph v1/v2 output parity with identical limits. Historical local diagnostic wall time only, not paired performance or full workflow gain. Frozen initial vs replay candidate sets only. Full event coverage includes UNKNOWN. No state updates, native run, heldout quality or complete workflow gains. Selected trees audited with original XML-derived Fraction increments; independent output verifier still required.')
(D/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='bindings'},indent=2),flush=True)
