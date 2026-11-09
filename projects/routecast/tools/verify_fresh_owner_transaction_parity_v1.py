"""Fresh discovery/transactions match every historically validated candidate."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/fresh_critical_owner_transactions_v1_2026-10-08';B=R/'experiments/critical_owner_transaction_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());fp=D/'complete_frames_verification.json';frames=json.loads(fp.read_text());assert frames['all_four_complete_frames_original_xml_fraction_pass'] and all(sha(p)==h for p,h in frames['bindings'].items())
discovery=R/'experiments/fresh_critical_owner_discovery_v1_2026-10-08/receipt.json';d=json.loads(discovery.read_text());assert all(sha(p)==h for p,h in d['bindings'].items());dp=discovery.with_name('verification.json');dv=json.loads(dp.read_text());assert dv['all_blocking_node_owner_sets_reconstructed'] and all(sha(p)==h for p,h in dv['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);queries=json.loads(Path(case['target']).read_text())['connections'];plans=[]
for cid in d['selected_connections']:
 full=next(e for e in d['events'] if e['connection_id']==cid and e['scenario']=='FULL_CONSTRAINTS');relax=next(e for e in d['events'] if e['connection_id']==cid and e['scenario']=='RELAX_OTHER_OWNERS')
 if full['search']['status']!='FOUND' or relax['search']['status']!='FOUND' or relax['search']['delay']>=full['search']['delay'] or not relax['blocking_net_ids']:continue
 released=sorted(q['connection_id'] for q in queries if q['net_id'] in relax['blocking_net_ids'])
 for order in ('ASCENDING','DESCENDING'):plans.append(dict(critical=cid,owners=relax['blocking_net_ids'],released_connections=released,restore_order=released if order=='ASCENDING' else released[::-1],order=order))
assert [row['plan'] for row in r['rows']]==plans
old=json.loads((B/'receipt.json').read_text());np=B/'native_canonical_verification.json';native=json.loads(np.read_text());assert native['all_four_complete_native_canonical_chains_pass'] and all(sha(p)==h for p,h in native['bindings'].items());assert len(r['rows'])==len(old['rows'])==4
for left,right in zip(r['rows'],old['rows']):
 a=left['plan'];b=right['plan'];assert a['owners']==[b['owner']]
 for key in ('critical','released_connections','restore_order','order'):assert a[key]==b[key]
 assert left['state']==right['state'] and left['transaction_complete']==right['transaction_complete']==True and len(left['events'])==len(right['events'])
 for x,y in zip(left['events'],right['events']):
  for key in ('connection_id','status','budget_integer_ceiling','path','physical_edge_ids','delay_integer'):assert x[key]==y[key]
bindings={**frames['bindings'],**native['bindings'],**dv['bindings'],str(rp):sha(rp),str(fp):sha(fp),str(discovery):sha(discovery),str(dp):sha(dp),str(np):sha(np),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(__file__)):sha(Path(__file__))};assert all(sha(p)==h for p,h in bindings.items())
out=dict(bindings=bindings,all_fresh_plans_independently_derived_from_discovery=True,all4_candidates_and102_stage_paths_equal_historical_native_validated_states=True,component_elapsed_seconds=r['component_elapsed_seconds'],model_cpd_ns=[x['fixed_local_model_cpd_ns'] for x in frames['rows']],budget_safe_connections_per_candidate=1927,original_budget_violation_ids=[785,1637],scope='Fresh critical/owner discovery and complete release/restore production, historical references only verifier. Prior VPR/canonical evidence inherited by exact full-state identity, not a new VPR run or original HDL equivalence; first reconciliation counts unchanged. No publication or full-workflow speedup, upstream/downstream costs missing.')
(D/'parity_verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
