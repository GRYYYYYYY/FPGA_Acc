"""Full actual endpoint delta and new-context versus independent rebuild scientific verification."""
import json,ast
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_whole_net_initial_cache_sequence_v1_2026-10-10';p=D/'verification.json';v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());protocol=json.loads((D/'protocol.json').read_text());assert all(sha(k)==h for k,h in protocol['bindings'].items());assert [r['arm'] for r in v['rows']]==['old_cold_context','first_warm_context','new_warm_context','new_original_rebuild'];oldmodel=R/'tools/run_resident_actual_old_linear_undo_model_v13.py';newmodel=R/'tools/run_resident_whole_net_initial_cache_model_v2.py';normalized=newmodel.read_text().replace('from owned_static_rr_context_v1 import load_endpoints','from class_cached_rc_endpoint_context_v1 import load_endpoints').replace('from whole_net_zero_price_search_cache_v2 import Search','from hybrid_bidirectional_search_v1 import Search').replace("\n search.configure_initial_groups(digest,queries,{p:h for p,h in bindings.items() if p!=str(endpoint) and p not in {v['path'] for v in json.loads(endpoint.read_text())['inputs'].values()}})",'').replace('Process-local zero-price complete-NET initial search cache, keyed by graph digest, RC scale, complete ordered queries and implementation bindings; no feedback state or native labels reused.','No archived floor/sketch/native labels read.');assert ast.dump(ast.parse(normalized))==ast.dump(ast.parse(oldmodel.read_text()));old=json.loads(Path(protocol['old_endpoints']).read_text());new=json.loads(Path(protocol['new_endpoints']).read_text());a={q['connection_id']:q for q in old['connections']};b={q['connection_id']:q for q in new['connections']};assert len(a)==len(b)==6273 and a.keys()==b.keys();changed={c for c in a if (a[c]['source'],a[c]['sink'])!=(b[c]['source'],b[c]['sink'])};assert changed==set(protocol['changed_connections']) and len(changed)==55;bindings={str(x):sha(x) for x in [Path(__file__).resolve(),p,D/'protocol.json',oldmodel,newmodel,Path(protocol['old_endpoints']),Path(protocol['new_endpoints'])]}
first={q['connection_id']:q for q in json.loads(Path(protocol['first_endpoints']).read_text())['connections']};bindings[protocol['first_endpoints']]=sha(protocol['first_endpoints']);
for arm,queries in [('old_cold_context',a),('first_warm_context',first),('new_warm_context',b),('new_original_rebuild',b)]:
 B=D/arm
 for filename in ['initial.json','sketch.json','round0.json','round1.json']:
  pp=B/'model'/filename;state=json.loads(pp.read_text());records={x['connection_id']:x for x in state['records']};assert records.keys()==queries.keys() and len(state['records'])==6273
  for cid,q in queries.items():assert {k:records[cid][k] for k in q}==q
  bindings[str(pp)]=sha(pp)
 for rel in ['handoff/receipt.json','model/receipt.json','model/shared_audit_receipt.json']:
  pp=B/rel;proof=json.loads(pp.read_text())
  for section in ['bindings','files']:assert all(sha(k)==h for k,h in proof.get(section,{}).items())
  bindings[str(pp)]=sha(pp)
 assert proof['all_three_complete_audits_pass'] and proof['fresh_independent_graph_context'] and proof['diagnostics']['independent_xml_parses']==2
 for filename in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  pp=B/'model'/filename;proof=json.loads(pp.read_text());assert all(sha(k)==h for k,h in proof['bindings'].items());assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings[str(pp)]=sha(pp)
 assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and proof['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
A=D/'new_warm_context';B=D/'new_original_rebuild'
for rel in ['model/initial.json','model/sketch.json','model/round0.json','model/round1.json','native/subset.json','native/bindings.json']:
 pp=A/rel;qq=B/rel;assert json.loads(pp.read_text())==json.loads(qq.read_text());bindings.update({str(pp):sha(pp),str(qq):sha(qq)})
x=json.loads((A/'model/receipt.json').read_text());y=json.loads((B/'model/receipt.json').read_text());assert x.keys()==y.keys() and len(x['rounds'])==len(y['rounds'])==2;events=0
for u,w in zip(x['rounds'],y['rounds']):assert u.keys()==w.keys() and {k:z for k,z in u.items() if k not in ['seconds','state_file']}=={k:z for k,z in w.items() if k not in ['seconds','state_file']};events+=len(u['events'])
assert (A/'native/seed.route').read_bytes()==(B/'native/seed.route').read_bytes()
for pp in [A/'native/seed.route',B/'native/seed.route']:bindings[str(pp)]=sha(pp)
def groups(qs):
 result={}
 for q in qs.values():result.setdefault(q['net_id'],[]).append(q)
 return result
for i,(prev,current) in enumerate([(a,first),(first,b)],1):
 pg,cg=groups(prev),groups(current);unchanged=sum(pg.get(net)==rows for net,rows in cg.items());changednets=len(cg)-unchanged
 before=v['rows'][i-1]['initial_cache'];after=v['rows'][i]['initial_cache']
 assert after.get('hits',0)-before.get('hits',0)==unchanged
 assert after['misses']-before['misses']==changednets
 assert after['cached_groups']==len(cg) and after['retained_query_records']==6273
 assert after['retained_parent_slots']<=after['limits']['parents']
assert v['rows'][0]['initial_cache'].get('hits',0)==0 and v['rows'][1]['initial_cache']['hits']>0;assert v['rows'][0]['owned_context']['loads']==v['rows'][1]['owned_context']['loads']==1 and v['rows'][0]['owned_context']['accesses']==1 and v['rows'][1]['owned_context']['accesses']==2 and v['rows'][2]['owned_context']['accesses']==3;assert all(sha(k)==h for k,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_records_allstates_match_current_endpoint=True,all55_second_layout_changed_physical_endpoint_ids_applied=True,all_new_states_and_handoff_equal_original_full_rebuild=True,all_new_feedback_events_equal=events,all3_complete_independent_audits_each_phase_pass=True,seed_bytes_equal=True,rows=v['rows'],scope='Actual legal swap static-context reuse full equivalence. Whole-NET zero-price initial searches reused for exact unchanged query groups; full feedback recomputed; no dynamic incremental path algorithm or fullnative/canonical/strictfamily/hardware gain. First cold-context cost retained.'),indent=2)+'\n');print('INDEPENDENT ACTUAL SWAP FULL PARITY',events)
