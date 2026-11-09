"""Authenticate first appearance of every final selected physical path."""
import json
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';mp=R/'tools/online_cost_replay_manifest_v6.json';m=json.loads(mp.read_text())['mapping'];bindings={**closure([Path(__file__)]),str(mp):sha(mp)}
def report(key):
 p=E/m.get(key,key)/'verification.json';d=json.loads(p.read_text());assert all(sha(p)==h for p,h in d['bindings'].items());bindings.update(d['bindings']);bindings[str(p)]=sha(p);return d
keys=['adder_online_candidate_bank_v1','adder_online_detour_bank_v1','adder_online_proof_expand_v1','adder_online_small_component_detours_v1','adder_online_owner337_detours_v1','adder_online_support_closure_v1','adder_online_leaf_context_search_v1']
snapshots=[]
for key in keys:
 p=E/m[key+'_2026-10-09']/'step_3.json';d=json.loads(p.read_text());bindings[str(p)]=sha(p);snapshots.append(d['bank'])
selection=report('adder_online_component_solve_v5_2026-10-09')['selection'];quality=report('adder_online_full_selection_verification_v1_2026-10-09');ablation=report('adder_online_leaf_ablation_verification_v1_2026-10-09');rows=[];counts=Counter();origins=Counter()
for cid,index in selection.items():
 option=snapshots[-1][cid][index];path=option['path'];first=next(k for k,bank in zip(keys,snapshots) if any(o['path']==path for o in bank[cid]));rows.append(dict(connection_id=int(cid),selected_index=index,origin=option['origin'],first_bank=first));counts[first]+=1;origins[option['origin']]+=1
assert len(rows)==516 and dict(origins)==quality['selected_origins'];assert counts['adder_online_leaf_context_search_v1']==1
assert len(ablation['rows'][0]['dead_leaves'])==12
assert all(sha(p)==h for p,h in bindings.items())
D=E/'adder_online_selected_provenance_v2_2026-10-09';D.mkdir(exist_ok=False);out=dict(bindings=bindings,connections=516,first_bank_counts=dict(counts),selected_origins=dict(origins),rows=rows,leaf_ablation='FINITE_BANK_EXHAUSTED_INDEPENDENT_12_LEAVES',scope='Final-path first appearance and one concrete candidate ablation. Nonselected intermediates can still guide later search; zero selected paths does not prove stage removable. Current fixed finite bank only, no full graph infeasibility or timing/performance claim.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('connections','first_bank_counts','selected_origins','leaf_ablation')},indent=2))
