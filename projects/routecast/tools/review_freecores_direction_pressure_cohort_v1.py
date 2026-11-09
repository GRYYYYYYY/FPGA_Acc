"""Authenticate complete four-arm pressure-polarity development cohort."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
bindings={str(Path(__file__)):sha(Path(__file__))}
def auth(obj):
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ('bindings','files') and isinstance(v,dict):
    for p,h in v.items():
     if p in bindings:assert bindings[p]==h,p
     bindings[p]=h
   else:auth(v)
 elif isinstance(obj,list):
  for v in obj:auth(v)
def load(p):
 d=json.loads(p.read_text());auth(d);bindings[str(p)]=sha(p);return d
protocol=load(R/'experiments/freecores_direction_pressure_model_v2_2026-10-08/protocol.json');assert protocol['cases']==['8051','xtea'] and protocol['modes']==['within_polarity','across_polarity']
rows=[]
for name,count in [('8051',16503),('xtea',2450)]:
 for mode in protocol['modes']:
  resident=R/'experiments/freecores_direction_pressure_model_v2_2026-10-08'/name/mode/'resident'
  for frame in ['initial','sketch']:
   p=load(resident/(frame+'_physical_verification.json'));assert p['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and p['completed']==count
  event=load(resident/'verification.json');assert event['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and event['actual_projected_price_changes_and_independent_groupmeans_pass'] and event['pressure_mode']==mode and event['completed']==count
  metrics=R/'experiments/freecores_direction_pressure_hotspots_v1_2026-10-08'/name/mode
  mp=load(metrics/'metric_verification.json');assert mp['histogram_ranks_topk_mae_and_full_vector_scope_pass'] and mp['metric_vectors_recomputed']==7
  comparison=load(metrics/'comparison.json');assert comparison['required']==comparison['completed']==count
  native=R/'experiments/freecores_direction_pressure_native_seed_v1_2026-10-08'/name/mode
  nr=load(native/'receipt.json');np=load(native/'verification.json');assert nr['exit_code']==0 and np['physical_connections']==count and np['overflow_units']==0 and np['all_physical_endpoints_original_XML_arcs_and_node_NET_capacity_pass'] and np['original_native_FULL_check_pass']
  assert nr['retained_connections']+nr['pending_connections']==count
  canonical=R/'experiments/freecores_direction_pressure_seed_canonical_v1_2026-10-08'/mode
  cr=load(canonical/'receipt.json');row=next(x for x in cr['rows'] if x['name']==name);assert row['status']=='SEMANTIC_CANONICAL_PASS' and row['canonical']['semantic_consistency_gate_pass']
  ip=load(canonical/'ignored_pin_verification_v1.json');ir=next(x for x in ip['rows'] if x['name']==name);assert ir['every_mismatch_matches_native_ignored_sink_pin'] and ir['post_reload_packed_netlist_byte_identical'] and not ir['strict_zero_counter_gate_pass']
  rows.append(dict(name=name,mode=mode,required=count,events=event['events'],model_overflow=event['overflow_units'],shared_metrics=comparison['metrics']['wire_shared'],native_iterations=np['iterations'],native_wirelength=nr['wirelength'],diagnostic_cpd_ns=nr['diagnostic_cpd_ns'],canonical_and_independent_ignored_pass=True,strict_zero_counter_gate_pass=False))
assert all(sha(k)==h for k,h in bindings.items())
out=R/'experiments/freecores_direction_pressure_cohort_review_v1_2026-10-08';out.mkdir()
(out/'review.json').write_text(json.dumps(dict(bindings=bindings,all_four_complete_development_arms_authenticated=True,rows=rows,conclusions=['Across-polarity pooling lowers shared spatial Spearman/top20 and worsens MAE in both cases relative to within-polarity control.','Native QoR is mixed: merged pressure increases wirelength in both, reduces XTEA iteration count, improves synthetic diagnostic8051 CPD.','Original strict zero-counter gate remains false; actual ignored-pin membership and packed bytes independently pass.'],pending=['Model component paired times and whole workflow gain/stability','Strict unseen-family isolation and original HDL equivalence','Characterized async timing and physical board execution'],scope='Known-label ceil-mean pressure resolution development control, not topology-direction erasure or unbiased direction-only causal proof. Same original graph/RC/budgets/full queries/fixed cold metric labels/native configuration. No baseline retuning or failed-arm omission. Research goal remains incomplete.'),indent=2)+'\n');print('Four full pressure-polarity cohort arms authenticated; QoR mixed')
