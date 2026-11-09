"""Authenticate every frozen development outcome and preserve mixed metrics."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
D=R/'experiments/freecores_no_ipin_cohort_review_v1_2026-10-08';D.mkdir();bindings={str(Path(__file__)):sha(Path(__file__))}
def read(path):
 bindings[str(path)]=sha(path);d=json.loads(path.read_text())
 for group in ['bindings','files']:
  assert all(sha(k)==h for k,h in d.get(group,{}).items());bindings.update(d.get(group,{}))
 return d
pre=read(R/'experiments/freecores_no_ipin_downstream_prereg_v1_2026-10-08/protocol.json');down=read(R/'experiments/freecores_no_ipin_downstream_v1_2026-10-08/receipt.json');assert down['all_stages_terminal_zero'] and len(down['rows'])==11
for row in down['rows']:assert row['exit_code']==0 and sha(row['log'])==row['log_sha256'];bindings[row['log']]=row['log_sha256']
comparison=read(R/'experiments/freecores_no_ipin_comparison_v1_2026-10-08/comparison.json');assert comparison['all_complete_cases_types_and_14_metric_vectors_authenticated']
canonical=R/'experiments/freecores_no_ipin_seed_canonical_v1_2026-10-08';cp=read(canonical/'receipt.json');ip=read(canonical/'ignored_pin_verification_v1.json');rows=[]
for name in pre['cases']:
 model=R/'experiments/freecores_no_ipin_dynamic_price_v1_2026-10-08'/name/'resident';mv=read(model/'verification.json');assert mv['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
 new=R/'experiments/freecores_no_ipin_native_seed_v1_2026-10-08'/name;r=read(new/'receipt.json');vp=read(new/'verification.json');assert r['exit_code']==0 and vp['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and vp['original_native_FULL_check_pass'] and vp['overflow_units']==0 and mv['completed']==r['required_connections']==vp['physical_connections'] and r['pending_connections']+r['retained_connections']==r['required_connections']
 cr=next(x for x in cp['rows'] if x['name']==name);assert cr['status']=='SEMANTIC_CANONICAL_PASS' and cr['canonical']['semantic_consistency_gate_pass'];assert all(sha(k)==h for k,h in cr['canonical']['files'].items());bindings.update(cr['canonical']['files']);pin=next(x for x in ip['rows'] if x['name']==name);assert pin['every_mismatch_matches_native_ignored_sink_pin'] and pin['post_reload_packed_netlist_byte_identical'];assert not pin['strict_zero_counter_gate_pass']
 bdir=R/'experiments/freecores_native_seed_v1_2026-10-08'/name;br=read(bdir/'receipt.json');bv=read(bdir/'verification.json');assert br['command']==r['command'] and br['required_connections']==r['required_connections']
 metrics=next(x for x in comparison['rows'] if x['name']==name)['methods'];rows.append(dict(name=name,prediction_and_typed_demand=metrics,native_baseline_seed=dict(iterations=bv['iterations'],wirelength=br['wirelength'],diagnostic_cpd_ns=br['diagnostic_cpd_ns'],native_seconds=br['native_process_seconds'],seed_preparation_seconds=br['seed_preparation_seconds']),native_no_ipin_seed=dict(iterations=vp['iterations'],wirelength=r['wirelength'],diagnostic_cpd_ns=r['diagnostic_cpd_ns'],native_seconds=r['native_process_seconds'],seed_preparation_seconds=r['seed_preparation_seconds'],retained_connections=r['retained_connections'],pending_connections=r['pending_connections']),canonical_pin_audit=pin))
assert all(sha(k)==h for k,h in bindings.items());result=dict(bindings=bindings,all_complete_cohort_prediction_native_physical_canonical_and_ignored_pin_checks_pass=True,rows=rows,scope='Frozen development price knockout, complete both cases retained. Native command/binary/RR/physical scope matched, historical baseline clocks are not contemporaneous continuous measurement. All CPD diagnostic uncharacterized async timings, nonzero ignored counters retained; no original HDL, strict-heldout, physical hardware or fullworkflow gain admission.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS complete no-IPIN development cohort',flush=True)
