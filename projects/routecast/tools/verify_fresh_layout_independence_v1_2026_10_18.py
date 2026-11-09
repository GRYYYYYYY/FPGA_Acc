"""Discarded archived dirty records must not affect transport-only layout."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from fresh_native_warm_prefix_v1 import prepare_layout
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_fresh_prefix_local_v1_2026-10-18/layout_independence_probe';D.mkdir(exist_ok=False)
original=R/'experiments/mmc_native_dirty_transition_recipe_v1_2026-10-18/dirty_recipe.json';payload=json.loads(original.read_text());payload['dirty_records']=[]
copy=D/'recipe_without_dirty_values.json'
with copy.open('x') as f:json.dump(payload,f)
proof=json.loads(original.with_suffix('.proof.json').read_text());proof['recipe']=str(copy);proof['bindings'][str(copy)]=sha(copy);proof['test_fixture_mutation']='Archived dirty records deliberately removed; layout metadata only.'
with copy.with_suffix('.proof.json').open('x') as f:json.dump(proof,f)
output=prepare_layout(copy,D/'layout.json');actual=R/'experiments/mmc_fresh_prefix_local_v1_2026-10-18/layout.json'
assert output.read_bytes()==actual.read_bytes() and 'dirty_records' not in json.loads(output.read_text())
with (D/'verification.json').open('x') as f:json.dump(dict(status='pass',archived_dirty_records_can_be_removed_without_layout_change=True,original_recipe_sha256=sha(original),actual_layout_sha256=sha(actual),probe_layout_sha256=sha(output),helper_source_sha256=sha(R/'tools/fresh_native_warm_prefix_v1.py')),f,indent=2)
print('PASS layout independent of all480archived dirty record values',flush=True)
