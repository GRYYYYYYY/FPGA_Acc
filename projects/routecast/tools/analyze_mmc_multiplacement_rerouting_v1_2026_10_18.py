"""Measure full native rerouting outside endpoint-dirty NET closure."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from affected_connections import affected
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths
D=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18';I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18';cp=D/'cohort_complete.json';assert json.loads(cp.read_text())['all3_cold_labels_admitted'];bindings={**closure([Path(__file__)]),str(cp):sha(cp),str(D/'evaluation_protocol.json'):sha(D/'evaluation_protocol.json')}
gp=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';g=json.loads(gp.read_text());old_ep=Path(g['previous_endpoint']);oldroute=Path(g['previous_native_route']);old=json.loads(old_ep.read_text());oldpaths=mapped_paths(old,oldroute);nets={q['connection_id']:q['net_id'] for q in old['connections']};rows=[]
for case in ['case_01','case_02','case_03']:
 proof=D/case/'verification.json';v=json.loads(proof.read_text());assert v['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(proof)]=sha(proof)
 new_ep=I/case/'demand/endpoints.json';new=json.loads(new_ep.read_text());delta=affected(old,new);declared=json.loads((I/case/'staged_input_verification_v1.json').read_text())['affected'];assert delta==declared
 paths=mapped_paths(new,D/case/'cold/output.route');assert paths.keys()==oldpaths.keys();changed={cid for cid in oldpaths if oldpaths[cid]!=paths[cid]};dirty=set(delta['affected_net_ids']);changed_nets={nets[cid] for cid in changed};outside={cid for cid in changed if nets[cid] not in dirty}
 rows.append(dict(case=case,direct_changed_connections=len(delta['changed_connection_ids']),endpoint_dirty_NETs=len(dirty),closure_connections=len(delta['recompute_connection_ids']),actual_changed_connection_paths=len(changed),actual_changed_NETs=len(changed_nets),changed_paths_outside_dirty_NETs=len(outside),changed_NETs_outside_dirty_NETs=len(changed_nets-dirty),outside_fraction_of_changed_paths=len(outside)/len(changed) if changed else 0,native_wirelength=v['rows'][0]['wirelength'],diagnostic_cpd_ns=v['rows'][0]['diagnostic_cpd_ns']))
 bindings[str(new_ep)]=sha(new_ep);print('DRIFT',rows[-1],flush=True)
for p in [gp,old_ep,oldroute]:bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'global_rerouting_diagnostic_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,scope='Exact path change versus original source, grouped by frozen endpoint closure. Descriptive full cold-router response; does not establish prediction errors, estimator ranking, causal source of interactions, heldout quality or timing gain.'),f,indent=2)
