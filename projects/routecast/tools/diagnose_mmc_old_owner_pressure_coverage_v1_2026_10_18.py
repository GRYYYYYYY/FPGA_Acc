"""Retrospective NET-union-change coverage of frozen pre-route owner pressure context."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
D=R/'experiments/mmc_old_owner_pressure_context_v1_2026-10-18';vp=D/'independent_selection_verification_v1.json';v=json.loads(vp.read_text());assert v['all3_pressure_sets_and_old_owner_NET_contexts_independently_equal'];bindings={**v['bindings'],str(vp):sha(vp),**closure([Path(__file__)])};selection=json.loads((D/'selection.json').read_text());g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());ep=json.loads(Path(g['previous_endpoint']).read_text());names={ep['net_names'][str(q['net_id'])]:q['net_id'] for q in ep['connections']}
def parse(path):
 unions={};current=None
 for line in Path(path).open():
  w=line.split()
  if w and w[0]=='Net':
   current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
   if current is not None:assert current in names and current not in unions;unions[current]=set()
  elif w and w[0]=='Node:':assert current in names;unions[current].add(int(w[1]))
 assert set(unions)==set(names);return unions
cache=Cache();rows=[];admitted={}
with cache.installed():
 assert all(sha(p)==h for p,h in bindings.items());oldroute=Path(g['previous_native_route']);old=parse(oldroute);assert bindings[str(oldroute)]==sha(oldroute)
 for case in ['case_01','case_02','case_03']:
  s=next(x for x in selection['rows'] if x['case']==case);selected=set(s['net_ids']);dirty=set(s['endpoint_NET_closure']);cold=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18'/case;warm=R/'experiments/mmc_partial_firstpass_recovery_v3_2026-10-18'/case
  for label,root,arm in [('cold',cold,'cold'),('partial_seed_default',warm,'off'),('partial_seed_firstpass_preserve',warm,'on')]:
   proof=(root/'verification.json').resolve()
   if str(proof) not in admitted:
    a=json.loads(proof.read_text());assert a['all_native_physical_and_canonical_pass'] and all(sha(p)==h for p,h in a['bindings'].items());admitted[str(proof)]=a;bindings.update(a['bindings']);bindings[str(proof)]=sha(proof)
   a=admitted[str(proof)];route=(root/arm/'output.route').resolve();physical=(root/arm/'physical_audit.json').resolve();assert a['bindings'][str(route)]==sha(route) and a['bindings'][str(physical)]==sha(physical);new=parse(route);ph=json.loads(physical.read_text());assert Counter(n for nodes in new.values() for n in nodes)==Counter({int(n):x for n,x in ph['node_occupancy'].items()});changed={names[n] for n in old if old[n]!=new[n]};assert changed;hit=len(selected&changed);rows.append(dict(case=case,label=label,selected_NETs=len(selected),selected_connections=s['connections'],endpoint_NET_closure=len(dirty),NET_schedule_expansion=len(selected)/len(dirty),changed_NET_node_unions=len(changed),selected_changed_NETs=hit,changed_NET_union_recall=hit/len(changed),changed_NET_unions_outside_context=len(changed-selected),selected_NET_union_change_precision=hit/len(selected)));bindings[str(route)]=sha(route);bindings[str(physical)]=sha(physical);print('OWNER CONTEXT COVERAGE',rows[-1],flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
with (D/'exposed_coverage_all3policies_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,digest=cache.snapshot(),selection_used_old_route_and_frozen_initial_forecast_only=True,coverage_labels_exposed=True,scope='Retrospective NET node-union-change coverage of already frozen context across all3placements and3native policies. Counter replay equals admitted physical ledgers. Union change is not exact pin-path/switch change, actual reroute identity or an accuracy bound. No changing selected contexts or selecting a favorable label; no timing, heldout or native QoR claim.'),f,indent=2)
