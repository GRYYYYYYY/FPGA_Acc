"""Real-snapshot metadata/path parity and failed-publication contracts."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from partial_seed_state import publish_partial_seed
from native_route_ledger_import_compact import physical_paths
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_partial_seed_state_contract_2026-10-07';out.mkdir(exist_ok=False);rows=[]
cases=[('mux',ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w16_c128/design.route',ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w16_m1/target_endpoints.json',ROOT/'experiments/native_resume_inventory_pipeline_w16_m1_workflow_2026-10-07/first_seed.route'),('adder',ROOT/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits/design.route',ROOT/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json',ROOT/'experiments/native_resume_adder_pipeline_v3_step3_workflow_2026-10-07/first_seed.route')]
for name,seed,ep,reference in cases:
 meta=json.loads(ep.read_text());place=Path(meta['inputs']['place']['path']);allpaths=physical_paths(seed);retained=physical_paths(reference);excluded={n for n,ps in allpaths.items() if ps and not retained.get(n)};target=out/(name+'.route');receipt=publish_partial_seed(seed,place,ep,excluded,target);assert target.read_bytes()==reference.read_bytes();rows.append(dict(case=name,byte_parity=True,receipt=receipt,bindings={str(f):sha(f) for f in (seed,ep,reference,target)}))
 before=sha(target)
 try:publish_partial_seed(seed,place,ep,excluded,target)
 except FileExistsError:pass
 else:raise AssertionError('overwrite accepted')
 assert sha(target)==before;rows.append(dict(case=name+'_existing_destination',existing_output_unchanged=True))
 if name=='adder':
  bad=json.loads(ep.read_text());bad['connections'][0]['sink']=-1;bad_ep=out/'bad_endpoint.json';bad_ep.write_text(json.dumps(bad));destination=out/'failed_endpoint.route'
  try:publish_partial_seed(seed,place,bad_ep,excluded,destination)
  except ValueError:pass
  else:raise AssertionError('bad endpoint published')
  assert not destination.exists() and not list(out.glob('.partial_seed_*'));rows.append(dict(case='invalid_endpoint',no_artifact_or_staging_left=True))
  bad_place=out/'bad.place';text=place.read_text();text='\n'.join(line for line in text.splitlines() if not line.startswith('sum0_0[19]\t'))+'\n';bad_place.write_text(text);bad=json.loads(ep.read_text());bad['inputs']['place']=dict(path=str(bad_place.resolve()),sha256=sha(bad_place));bad_ep=out/'bad_global_endpoint.json';bad_ep.write_text(json.dumps(bad));destination=out/'failed_global.route'
  try:publish_partial_seed(seed,bad_place,bad_ep,excluded,destination)
  except ValueError as e:assert 'global block missing' in str(e)
  else:raise AssertionError('missing block accepted')
  assert not destination.exists() and not list(out.glob('.partial_seed_*'));rows.append(dict(case='missing_global_block',no_artifact_or_staging_left=True))
(out/'receipt.json').write_text(json.dumps(dict(rows=rows,producer_sha256=sha(Path(__file__)),adapter_sha256=sha(Path(__file__).parent/'partial_seed_state.py')),indent=2)+'\n');print([{k:v for k,v in r.items() if k not in ('receipt','bindings')} for r in rows])
