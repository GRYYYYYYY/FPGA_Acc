"""Full source-factor boundaries, current query scope, all complete independent audit receipts."""
import ast,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];T=R/'tools';D=R/'experiments/sha_price_factorial_ablation_v2_2026-10-10'
def auth(v):
 for section in ['bindings','files']:
  assert all(sha(p)==h for p,h in v.get(section,{}).items())
def equal(a,b):assert ast.dump(ast.parse(a))==ast.dump(ast.parse(b))
bindings={str(Path(__file__)):sha(Path(__file__))};base=(T/'run_resident_actual_old_linear_undo_model_v13.py').read_text()
for mode,span,overuse in [('no_span',False,True),('no_overuse',True,False),('neither',False,False)]:
 desc=f'Frozen ablation: span={span}, overuse={overuse}; original CHAN first-round schedule preserved; zero-price initial floor unchanged'
 p=T/f'run_resident_price_ablation_{mode}_v1.py';s=p.read_text();s=s.replace(f'static_channel_span_price_ns={desc!r}',"static_channel_span_price_ns='1/20 per destination CHAN span, applied in feedback only; initial remains exact zero-price RC floor'").replace(f'prices=Counter(span_prices if {span!r} else {{}});','prices=Counter(span_prices);').replace(f'prices.update(changed if {overuse!r} else {{}});','prices.update(changed);');equal(s,base);bindings[str(p)]=sha(p)
 for original in ['verify_resident_events_actual_old_joint_fallback_linear_v9.py','verify_resident_events_actual_old_linear_direct_lattice_v12.py']:
  p=T/(Path(original).stem+'_'+mode+'.py');s=p.read_text().replace(f"assert p['static_channel_span_price_ns']=={desc!r}","assert p['static_channel_span_price_ns']=='1/20 per destination CHAN span, applied in feedback only; initial remains exact zero-price RC floor'").replace(f'prices.update(span_prices if {span!r} else {{}});','prices.update(span_prices);').replace(f'prices.update(changed if {overuse!r} else {{}});','prices.update(changed);');equal(s,(T/original).read_text());bindings[str(p)]=sha(p)
for filename in ['receipt.json','protocol.json']:
 p=D/filename;v=json.loads(p.read_text());auth(v);bindings[str(p)]=sha(p)
r=json.loads((D/'receipt.json').read_text());assert r['all8complete_models_and_independent_audits_pass'];assert [(x['case'],x['mode']) for x in r['rows']]==[(c,m) for c in ['original','second_swap'] for m in ['both','no_span','no_overuse','neither']]
for case in ['original','second_swap']:
 initial=None;floors=None
 for row in [x for x in r['rows'] if x['case']==case]:
  assert row['codes']==[0,0];W=D/case/row['mode']/'model';queries={q['connection_id']:q for q in json.loads(Path(row['endpoint']).read_text())['connections']};assert len(queries)==6273
  for filename in ['initial.json','sketch.json','round0.json','round1.json']:
   p=W/filename;v=json.loads(p.read_text());records={x['connection_id']:x for x in v['records']};assert len(v['records'])==len(records)==6273 and records.keys()==queries.keys()
   for cid,q in queries.items():assert {k:records[cid][k] for k in q}==q
   bindings[str(p)]=sha(p)
  seed=json.loads((W/'initial.json').read_text());f=json.loads((W/'floors.json').read_text())
  if initial is None:initial=seed;floors=f
  else:assert seed==initial and f==floors
  for filename in ['receipt.json','protocol.json','initial_physical_verification.json','sketch_physical_verification.json','verification.json','shared_audit_receipt.json']:
   p=W/filename;v=json.loads(p.read_text());auth(v);bindings[str(p)]=sha(p)
   if filename in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
   if filename=='verification.json':assert v['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and v['complete_fallback_attempt_membership_actual_old_objective_and_budget_checks_pass']
   if filename=='shared_audit_receipt.json':assert v['all_three_complete_audits_pass'] and v['fresh_independent_graph_context'] and v['diagnostics']['independent_xml_parses']==2
assert all(sha(p)==h for p,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all8_full_query_models_and_complete_audits_pass=True,all_declared_price_only_source_deltas_pass=True,all4_initial_states_and_floors_equal_per_layout=True,scope='Fixed2x2 price policies with identical first-round scheduling/fullmodel/audits. No selected-best policy, heldout/causal outside these cases/native or fullworkflow speed proof.'),indent=2)+'\n');print('INDEPENDENT FULL PRICE FACTORIAL PASS')
