"""Exact selected seed path survival and complete old-state invalidation scope."""
import json,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from actual_change_budget_recheck_v1_2026_10_18 import mapped_paths
def owners(path,meta):
 names={name:int(net) for net,name in meta['net_names'].items()};result={};current=None
 for line in Path(path).open():
  words=line.split()
  if words and words[0]=='Net':
   name=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None;current=names[name] if name is not None else None
   if current is not None:assert current not in result;result[current]=set()
  elif words and words[0]=='Node:':assert current is not None;result[current].add(int(words[1]))
 return result
D=R/'experiments/mmc_v2_native_utility_v1_2026-10-18';S=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18';cp=D/'cohort_complete.json';C=json.loads(cp.read_text());assert C['all15_native_FULL_physical_and_canonical_semantic_pass'];bindings={**C['bindings'],**closure([Path(__file__)]),str(cp):sha(cp)};P=json.loads((S/'protocol.json').read_text());g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());oldmeta=json.loads(Path(g['previous_endpoint']).read_text());oldpaths=mapped_paths(oldmeta,Path(g['previous_native_route']));oldowners=owners(g['previous_native_route'],oldmeta);nets={q['connection_id']:q['net_id'] for q in oldmeta['connections']};rows=[];cache=Cache()
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items())
 for case in P['case_order']:
  I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case;epfile=I/'demand/endpoints.json';ep=json.loads(epfile.read_text());dirty=set(json.loads((I/'staged_input_verification_v1.json').read_text())['affected']['affected_net_ids']);vp=D/case/'verification.json';v=json.loads(vp.read_text());assert v['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(vp)]=sha(vp)
  for arm in P['native_arm_order']:
   final=mapped_paths(ep,D/case/arm/'output.route');changed={cid for cid in oldpaths if oldpaths[cid]!=final[cid]};changednets={nets[c] for c in changed};newowners=owners(D/case/arm/'output.route',ep);physical=json.loads((D/case/arm/'physical_audit.json').read_text());assert Counter(n for nodes in newowners.values() for n in nodes)==Counter({int(n):v for n,v in physical['node_occupancy'].items()});ownerchanged={n for n in set(oldowners)|set(newowners) if oldowners.get(n,set())!=newowners.get(n,set())};allchanged=changednets|ownerchanged;row=dict(case=case,arm=arm,connections_changed_from_old_native=len(changed),NETs_with_changed_terminal_paths=len(changednets),NETs_with_changed_printed_owner_node_sets=len(ownerchanged),NETs_in_union_of_detected_changes=len(allchanged),changed_NETs_outside_endpoint_closure=len(allchanged-dirty))
   if arm!='cold':
    W=S/case/arm;receipt=json.loads((W/'receipt.json').read_text());selected=set(receipt['selected_connection_ids']) if arm=='trim' else {r['connection_id'] for r in json.loads((W/'subset.json').read_text())['records']};seedmeta=dict(ep,connections=[q for q in ep['connections'] if q['connection_id'] in selected]);seed=mapped_paths(seedmeta,W/'seed.route');assert seed.keys()==selected and selected<=final.keys();preserved={cid for cid in selected if seed[cid]==final[cid]};selectednets={nets[c] for c in selected};changedseednets={nets[c] for c in selected-preserved};row.update(selected_connections=len(selected),pending_connections=115572-len(selected),selected_paths_preserved=len(preserved),selected_paths_changed=len(selected-preserved),selected_path_survival_fraction=len(preserved)/len(selected),whole_selected_NETs_preserved=len(selectednets-changedseednets),whole_selected_NETs_changed=len(changedseednets));assert row['pending_connections']==receipt['pending_connections']
   rows.append(row);print('SEED SURVIVAL',row,flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'seed_path_survival_and_owner_scope_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,scope='Exact CID original-node/switch path equality; all pending queries remain complete native work. Preserved paths may still have been rerouted, so survival does not prove no processing. Printed NET owner-node unions are compared in addition to terminal paths; no full reconstruction of unused nonterminal edges or complete native-memory invalidation guarantee; not a native-memory transaction/latency/heldout or forecast promotion claim.'),f,indent=2)
