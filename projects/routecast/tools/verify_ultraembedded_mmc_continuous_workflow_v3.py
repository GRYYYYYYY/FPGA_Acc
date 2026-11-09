"""Authenticate both continuous arms, all cases and complete scientific gates."""
import json,sys,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/ultraembedded_mmc_continuous_workflow_v3_2026-10-08'
def load(path):return json.loads(path.read_text())
def auth(data):
 for section in ['bindings','files']:
  for path,digest in data.get(section,{}).items():assert sha(path)==digest,(path,section)
r=load(D/'receipt.json');p=load(D/'protocol.json');auth(r);auth(p)
assert p['optimization']=='radix_v3 model and canonical multivalue pin index v2 in both arms; complete audits retained'
assert p['cases']==['mmc'] and [x['arm'] for x in r['rows']]==['cold','seed'] and all(x['status']=='COMPLETE_VERIFIED' and x['continuous_arm_seconds']>0 for x in r['rows'])
bindings={str(D/'receipt.json'):sha(D/'receipt.json'),str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(Path(__file__))};cases=[]
for name in p['cases']:
 arms={}
 for mode in p['arm_order']:
  b=D/mode;rr=b/'rr'/name;front=b/'demand'/name;native=b/'native'/name;canonical=b/'canonical'
  proofs=[rr/'verification.json',front/'verification.json',native/'verification.json',canonical/'ignored_pin_verification_v1.json']
  for path in proofs:
   proof=load(path);auth(proof);bindings[str(path)]=sha(path)
  assert load(rr/'verification.json')['complete_manifest_query_partition_and_original_XML_node_type_class_capacity_bbox_pass']
  assert load(front/'verification.json')['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass']
  physical=load(native/'verification.json');assert physical['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and physical['original_native_FULL_check_pass'] and physical['overflow_units']==0
  cp=load(canonical/'receipt.json');cr=next(x for x in cp['rows'] if x['name']==name);assert cr['status']=='SEMANTIC_CANONICAL_PASS' and cr['canonical']['semantic_consistency_gate_pass'];auth(cr['canonical']);bindings[str(canonical/'receipt.json')]=sha(canonical/'receipt.json')
  ip=next(x for x in load(proofs[-1])['rows'] if x['name']==name);assert ip['every_mismatch_matches_native_ignored_sink_pin'] and ip['post_reload_packed_netlist_byte_identical']
  receipt=load(native/'receipt.json');auth(receipt);bindings[str(native/'receipt.json')]=sha(native/'receipt.json');required=len(load(front/'endpoints.json')['connections']);assert required==115572 and physical['physical_connections']==required
  if mode=='seed':
   model=b/'model'/name
   for f in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
    path=model/f;proof=load(path);auth(proof);bindings[str(path)]=sha(path)
    assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
   assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and proof['completed']==required
   assert proof['events']==98479 and proof['committed']==98334 and proof['retained']==145
   subset=load(native/'subset.json');assert len(subset['records'])+len(subset['pending'])==required
   assert (native/'seed.route').is_file()
  else:assert not (native/'seed.route').exists() and not (b/'model').exists()
  arms[mode]=dict(required=required,rr_sha256=sha(rr/'rr_graph.xml'),input_sha256={f:sha(rr/f) for f in ['design.blif','design.net','design.place']},command=receipt['command'],native_seconds=receipt['native_process_seconds'],iterations=physical['iterations'],wirelength=receipt['wirelength'],diagnostic_cpd_ns=receipt['diagnostic_cpd_ns'])
 c,s=arms['cold'],arms['seed'];assert c['required']==s['required'] and c['rr_sha256']==s['rr_sha256'] and c['input_sha256']==s['input_sha256']
 def normalize(cmd):
  cmd=cmd.copy();cmd[cmd.index('--read_rr_graph')+1]='FRESH_MATCHED_GRAPH';return cmd
 assert normalize(c['command'])==normalize(s['command'])
 cases.append(dict(name=name,arms=arms))
ct,st=[x['continuous_arm_seconds'] for x in r['rows']];assert all(sha(k)==v for k,v in bindings.items())
result=dict(bindings=bindings,all_cases_both_complete_arms_authenticated=True,cases=cases,cold_continuous_cohort_seconds=ct,seed_continuous_cohort_seconds=st,seed_over_cold_ratio=st/ct,observed_single_trial_continuous_time_gain=st<ct,scope='Full single MMC frozen fixed-placement harness; single cold-then-seed wall timer reported by producer code, not independently reconstructed from per-stage clocks. RR XML and fixed input bytes equal across fresh arms. Validation included. No fastest conventional cold/replicate stability/HDL/real async timing/strict-heldout/silicon proof. Nonzero ignored-pin counters remain explicit.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','cases']},indent=2))
