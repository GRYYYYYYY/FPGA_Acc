"""Explicit reversible context-only changes; preserve certified original versions."""
from pathlib import Path
import json,ast
R=Path(__file__).resolve().parents[1]
model=[
('from structural_objective_search_v1 import Search','from sparse_structural_objective_search_v1 import Search\nfrom present_occupancy_context_v1 import Context'),
('structural_objective_contract_v1_2026-10-10','sparse_structural_objective_contract_v1_2026-10-10'),
('node_base,base_bindings=load_node_base',"context_contract=R/'experiments/present_occupancy_context_contract_v1_2026-10-10/verification.json';context_proof=json.loads(context_contract.read_text());assert context_proof['all_owner_exclusion_prices_minimum_objectives_and_finish_rebuilds_pass'] and context_proof['shared_fallback_same_snapshot_and_raw_budget_fixture_pass'] and all(sha(p)==h for p,h in context_proof['bindings'].items());bindings.update(context_proof['bindings']);bindings[str(context_contract)]=sha(context_contract);node_base,base_bindings=load_node_base"),
('structural_node_base_proof=str(NODE_BASE_PROOF),',"present_cost_policy='base[n]*max(0,other_occupancy-capacity+1), factor1, wholeNET old owner excluded at query snapshot; history unchanged',structural_node_base_proof=str(NODE_BASE_PROOF),"),
('rounds=[]\n for round_index',"rounds=[];context=Context(search,f['capacities'],node_base,len(groups));occupancy_context_seconds=0.0\n for round_index"),
('search.prepare(prices,weight);','context.start_round(prices,weight,ledger);'),
('search_tick=time.perf_counter();raw,parents,settled=search.search',"context_tick=time.perf_counter();snapshot=context.begin(owned[net]);context_updates={};occupancy_context_seconds+=time.perf_counter()-context_tick;search_tick=time.perf_counter();raw,parents,settled=search.search"),
('event=dict(net_id=net,','event=dict(occupancy_snapshot_ticket=context.ticket,net_id=net,'),
('settled,prices,weight,node_base,10000)','settled,snapshot,1,node_base,10000)'),
("event['records']=candidate\n","event['records']=candidate;context_updates=updates\n"),
('   assert record_count==len(queries);events.append(event)',"   context_tick=time.perf_counter();context.finish(context_updates);occupancy_context_seconds+=time.perf_counter()-context_tick;event['occupancy_snapshot_ended']=True\n   assert record_count==len(queries);events.append(event)"),
('check_tick=time.perf_counter();assert record_count','check_tick=time.perf_counter();assert context.active is None and context.ledger==ledger;assert record_count'),
('fallback_seconds=fallback_seconds,ledger_check_seconds=','occupancy_context_seconds=occupancy_context_seconds,fallback_seconds=fallback_seconds,ledger_check_seconds='),
('Initialized native structural cost, original hybrid path policy; initial floors exclude base, feedback and joint fallback include base.','Initialized native structural plus perquery current occupancy snapshot; wholeNET virtual release; factor1; original RC floors and raw budgets.')]
auditor=[
('checked=committed=retained=changed_trees=0',"checked=committed=retained=changed_trees=0;snapshot_count=0\nassert p['present_cost_policy']=='base[n]*max(0,other_occupancy-capacity+1), factor1, wholeNET old owner excluded at query snapshot; history unchanged'"),
('+node_base[e.sink]', '+node_base[e.sink]+node_base[e.sink]*max(0,ledger.get(e.sink,0)-(e.sink in transaction_old_nodes)-xml.graph.nodes[e.sink].capacity+1)'),
("net=event['net_id'];old=records[net];","snapshot_count+=1;assert event['occupancy_snapshot_ticket']==snapshot_count and event['occupancy_snapshot_ended'] is True\n  net=event['net_id'];old=records[net];transaction_old_nodes=ownership(old);"),
('complete_structural_node_cost_original_XML_and_float32_bits_rebuild_pass=True,','complete_present_snapshot_owner_exclusion_and_union_objective_pass=True,complete_structural_node_cost_original_XML_and_float32_bits_rebuild_pass=True,')]
for old,new,changes in [('run_structural_overflow_guard_model_v1.py','run_present_overflow_guard_model_v1.py',model),('verify_structural_guard_events_v1.py','verify_present_guard_events_v1.py',auditor)]:
 original=(R/'tools'/old).read_text();candidate=original
 for a,b in changes:
  assert candidate.count(a)==1,(a,candidate.count(a));candidate=candidate.replace(a,b)
 restored=candidate
 for a,b in reversed(changes):
  assert restored.count(b)==1;restored=restored.replace(b,a)
 assert restored==original;ast.parse(candidate);(R/'tools'/new).write_text(candidate)
O=R/'experiments/present_guard_source_qualification_v1_2026-10-10';O.mkdir(exist_ok=False)
(O/'edits.json').write_text(json.dumps(dict(model=model,auditor=auditor),indent=2)+'\n')
print('REVERSIBLE PRESENT CONTEXT SOURCES PASS')
