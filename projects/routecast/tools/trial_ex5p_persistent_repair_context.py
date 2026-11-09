"""In-process staged repair replay using one immutable graph/native context."""
import json,shutil,time,runpy,sys
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_persistent_repair_context_2026-10-06';out.mkdir();replay=root/'work/ex5p_persistent_repair_context_2026-10-06';replay.mkdir();shutil.copytree(root/'tools',replay/'tools',ignore=shutil.ignore_patterns('__pycache__'));(replay/'build').symlink_to(root/'build',target_is_directory=True);(replay/'experiments').mkdir()
shutil.copytree(root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06',replay/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06')
names=['nonzero_rc_ex5p_joint_delay','ex5p_frontier_repair','ex5p_bounded_history_repair','ex5p_budget_repair'];protocol={'stages':names,'endpoint_sha256':sha(root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json'),'sources':{name:sha(root/'tools'/name) for s in names for name in ('trial_'+s+'.py','verify_'+s+'.py')},'policy':'Unchanged staged development policies. One shared XML/CSR/IntegerRC/native arrays; constructor boundary resets other demand and costs. Independent XML verifiers between stages. No cached native answer/path and no native reference route reads. Staging excluded from timing; not unified production transaction or net acceleration proof.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
import nonzero_rc_endpoint_context as context_module
import native_capacity_rc_search as native_module
original_load=context_module.load_endpoints;original_native=native_module.NativeCapacityRC
start=time.monotonic();context=original_load(replay/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json');native=original_native(context[4]);setup=time.monotonic()-start;calls={'load':0,'native':0}
def reuse_load(ep):
 assert sha(ep)==protocol['endpoint_sha256'];calls['load']+=1;return context
def reuse_native(rc):
 assert rc is context[4];calls['native']+=1;native.set_other({})
 for i,c in enumerate(rc.fields['costs']):native.arrays[3][i]=c
 return native
context_module.load_endpoints=reuse_load;native_module.NativeCapacityRC=reuse_native
rows=[];begin=time.monotonic()
try:
 for name in names:
  t=time.monotonic();runpy.run_path(str(replay/'tools'/('trial_'+name+'.py')),run_name='__main__');elapsed=time.monotonic()-t
  t=time.monotonic();runpy.run_path(str(replay/'tools'/('verify_'+name+'.py')),run_name='__main__');audit=time.monotonic()-t
  actual=json.loads((replay/'experiments'/ (name+'_2026-10-06')/'receipt.json').read_text());baseline=json.loads((root/'experiments'/(name+'_2026-10-06')/'receipt.json').read_text())
  # Exclude location/digest/timing metadata only; every algorithmic event/path/state must match.
  keys=[k for k in baseline if not k.endswith('_sha256') and not k.endswith('_seconds')]
  assert all(actual[k]==baseline[k] for k in keys),name
  rows.append({'stage':name,'workflow_s':elapsed,'audit_s':audit,'semantic_keys':keys,'receipt_sha256':sha(replay/'experiments'/(name+'_2026-10-06')/'receipt.json'),'verification_sha256':sha(replay/'experiments'/(name+'_2026-10-06')/'verification.json')})
finally:
 context_module.load_endpoints=original_load;native_module.NativeCapacityRC=original_native
assert calls=={'load':4,'native':4}
result={'stages':rows,'context_initialization_s':setup,'replay_wall_s':time.monotonic()-begin,'workflow_with_initialization_s':setup+sum(x['workflow_s'] for x in rows),'audit_s':sum(x['audit_s'] for x in rows),'one_context_four_stages':True,'calls':calls,'replay_root':str(replay),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
