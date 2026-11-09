"""Descriptive recall/cost of frozen old-only spatial context selection."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_old_route_spatial_context_v1_2026-10-18';vp=D/'independent_selection_verification_v1.json';v=json.loads(vp.read_text());assert v['status']=='pass' and all(sha(p)==h for p,h in v['bindings'].items());bindings={**v['bindings'],**closure([Path(__file__)]),str(vp):sha(vp)};selection=json.loads((D/'selection.json').read_text());N=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18';dp=N/'global_rerouting_diagnostic_v1.json';diag=json.loads(dp.read_text());ivp=N/'rerouting_union_independent_verification_v2.json';iv=json.loads(ivp.read_text());assert iv['status']=='pass';bindings[str(dp)]=sha(dp);bindings[str(ivp)]=sha(ivp)
g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());oldmeta=json.loads(Path(g['previous_endpoint']).read_text());names={oldmeta['net_names'][str(q['net_id'])]:q['net_id'] for q in oldmeta['connections']}
def parse(path):
 unions={};current=None
 for line in Path(path).open():
  words=line.split()
  if words and words[0]=='Net':
   current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
   if current is not None:assert current in names and current not in unions;unions[current]=set()
  elif words and words[0]=='Node:':assert current in names;unions[current].add(int(words[1]))
 assert set(unions)==set(names);return unions
old=parse(g['previous_native_route']);rows=[]
for case in ['case_01','case_02','case_03']:
 route=N/case/'cold/output.route';assert sha(route)==iv['bindings'][str(route)];new=parse(route);changed={names[n] for n in old if old[n]!=new[n]};ref=next(x for x in diag['rows'] if x['case']==case);assert len(changed)==ref['actual_changed_NETs'];changed_outside=ref['changed_NETs_outside_dirty_NETs']
 for row in [x for x in selection['rows'] if x['case']==case]:
  selected=set(row['net_ids']);hit=len(selected&changed);endpoint_count=row['endpoint_NET_closure_count'];rows.append(dict(case=case,radius=row['radius'],selected_NETs=len(selected),selected_connections=row['connections'],scheduled_two_round_events=2*len(selected),NET_schedule_expansion=len(selected)/endpoint_count,changed_NETs_total=len(changed),selected_changed_NETs=hit,changed_NET_recall=hit/len(changed),selected_NET_change_precision=hit/len(selected),scope='NET-union-change recall on exposed labels, not estimator quality or runtime benefit.'))
 bindings[str(route)]=sha(route)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'exposed_coverage_diagnostic_v1.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,selection_used_only_old_inputs=True,coverage_labels_exposed=True,scope='Descriptive evaluation of previously frozen old-only selections. No causal/heldout accuracy claim and no radius switching for promotion.'),f,indent=2)
print('PRIMARY RADIUS2 COVERAGE',[(x['case'],x['selected_NETs'],x['changed_NET_recall'],x['NET_schedule_expansion']) for x in rows if x['radius']==2],flush=True)
