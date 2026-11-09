"""Disjoint phase accounting after balanced resident model comparison."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_resident_digest_abba_v1_2026-10-18';vp=D/'verification.json';v=json.loads(vp.read_text());assert v['status']=='pass' and v['all_full_frame_and_certificate_or_event_reference_checks_pass']
rows=[];receipts={};bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)}
for row in v['rows']:
 p=Path(row['output'])/'receipt.json';r=json.loads(p.read_text());bindings[str(p)]=sha(p);receipts[row['index']]=r
 if row['arm']=='local':
  main={k:r[k] for k in ['model_setup_seconds','initial_seconds','feedback_seconds']}
  assert abs(sum(main.values())-r['total_paid_resident_seconds'])<.1
  nested={k:r[k] for k in ['cpp_prepare_seconds','search_seconds','occupancy_context_seconds','fallback_seconds','ledger_check_seconds']}
  unassigned=main['feedback_seconds']-sum(nested.values());assert unassigned>=0
  bound={p:Path(p).stat().st_size for p in r['bindings']}
  rows.append(dict(index=row['index'],arm='local',complete_call_seconds=row['complete_call_seconds'],digest_delta=row['digest_delta'],main_disjoint=main,feedback_nested_disjoint=nested,feedback_unattributed_seconds=unassigned,unique_bound_path_bytes=sum(bound.values()),unique_bound_path_count=len(bound),static_binding_footprint_scope='Sum file sizes by unique bound path only; not measured actual hashed byte count, I/O time or causal phase attribution.'))
 else:rows.append(dict(index=row['index'],arm='raw',complete_call_seconds=row['complete_call_seconds'],search_and_certificate_seconds=r['dirty_search_and_certificates_seconds']))
optimistic=[]
for pair in v['pairs']:
 r=receipts[pair['local_index']];removed=sum(r[k] for k in ['cpp_prepare_seconds','search_seconds','fallback_seconds'])
 lower=pair['local_seconds']-removed
 optimistic.append(dict(raw_index=pair['raw_index'],local_index=pair['local_index'],removed_primary_fallback_price_prepare_seconds=removed,remaining_local_call_seconds=lower,raw_complete_seconds=pair['raw_seconds'],remaining_local_still_slower=lower>pair['raw_seconds'],scope='Optimistic zero cost for measured primary, whole fallback and price-prepare intervals with all other code unchanged. Not proposed hardware/runtime prediction or full-workflow bound.'))
result=dict(bindings=bindings,rows=rows,optimistic_component_removal=optimistic,local_latency_gate_pass=v['local_resident_latency_gate_pass'],scope='Measured balanced resident callback phases only, nested times not added twice. Does not identify all unattributed work, eliminate startup floor costs, prove end-to-end speed or generalize to unseen designs.')
with (D/'phase_cost_analysis_v1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:x for k,x in result.items() if k!='bindings'}),flush=True)
