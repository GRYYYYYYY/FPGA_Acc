"""Full MMC parity with existing loaders and mismatched-input rejection."""
import json,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
from load_design_routing_inputs_v1 import load
from load_structural_node_base_v1 import load as old_base,PROOF
from load_initial_connection_criticalities_v1 import load as old_criticalities
R=Path(__file__).resolve().parents[1]
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
crit=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10'
values,cs,bindings=load(ep,PROOF,crit,904438,10**18)
old,old_bindings=old_base(904438,10**18)
assert values==old and cs==old_criticalities(crit)
rejections=[]
for n,scale in [(904437,10**18),(904438,10**9)]:
 try:load(ep,PROOF,crit,n,scale)
 except ValueError as e:
  assert str(e)=='node-base domain, scale or byteorder mismatch';rejections.append(str(e))
 else:raise AssertionError('invalid domain accepted')
with tempfile.TemporaryDirectory(prefix='routecast_design_input_') as td:
 # Equal bytes at an unauthenticated endpoint path cannot silently change the binding contract.
 other=Path(td)/'endpoints.json';other.write_bytes(ep.read_bytes())
 try:load(other,PROOF,crit,904438,10**18)
 except ValueError as e:
  assert str(e)=='proof does not bind requested endpoint snapshot';rejections.append(str(e))
 else:raise AssertionError('unbound snapshot accepted')
bindings.update(old_bindings);bindings.update(closure([Path(__file__)]))
assert all(sha(p)==h for p,h in bindings.items())
out=R/'experiments/retained_tree_cross_design_readiness_v1_2026-10-13/loader_mmc_parity_v1.json'
with out.open('x') as f:json.dump(dict(bindings=bindings,nodes=len(values),connections=len(cs),all_existing_node_costs_and_criticalities_equal=True,rejections=rejections,scope='Full existing MMC input parity and mismatched domain/scale/path rejection; no second-design execution or heldout validation.'),f,indent=2)
print('PASS',len(values),'node costs;',len(cs),'criticalities; three mismatched inputs rejected',flush=True)
