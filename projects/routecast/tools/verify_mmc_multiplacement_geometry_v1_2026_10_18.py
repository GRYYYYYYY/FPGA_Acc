"""Independently check frozen cohort membership and geometry HPWL arithmetic."""
import json,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18';cp=D/'cohort_protocol.json';c=json.loads(cp.read_text());assert c['case_count']==3 and not c['target_labels_generated'];assert all(sha(p)==h for p,h in c['bindings'].items());bindings={**c['bindings'],**closure([Path(__file__)]),str(cp):sha(cp)}
first=json.loads(Path(c['cases'][0]).read_text());ep=json.loads(Path(first['previous_endpoint']).read_text());src=Path(ep['inputs']['net']['path']).parent
positions={}
for line in (src/'design.place').read_text().splitlines():
 w=line.split()
 if len(w)>=6:
  try:positions[w[0]]=tuple(int(x.lstrip('#')) for x in w[1:6])
  except ValueError:pass
mapping=json.loads((src/'mapping.json').read_text());included={q['net_id'] for q in ep['connections']};nets=defaultdict(set)
for pin in mapping['pin_details']:
 if pin['net_id'] in included:nets[pin['net_id']].add(pin['block'])
used=set(c['excluded_prior_pair']);rows=[]
for path in c['cases']:
 p=json.loads(Path(path).read_text());bindings[path]=sha(path);sel=p['selected'];pair=sel['pair'];assert len(pair)==2 and len(set(pair))==2 and not used.intersection(pair);used.update(pair);assert sel['block_ids']==[positions[n][4] for n in pair];a,b=pair
 assert all(list(positions[n])==sel['before_positions'][n] for n in pair)
 expected={a:(*positions[b][:4],positions[a][4]),b:(*positions[a][:4],positions[b][4])};assert all(list(expected[n])==sel['after_positions'][n] for n in pair)
 changed=dict(positions,**expected);touch={net for net,blocks in nets.items() if set(pair)&blocks};assert sorted(touch)==sel['touched_physical_nets']
 def cost(pos):
  total=0
  for net in touch:
   xs=[pos[n][0] for n in nets[net]];ys=[pos[n][1] for n in nets[net]];total+=max(xs)-min(xs)+max(ys)-min(ys)
  return total
 delta=cost(changed)-cost(positions);assert delta==sel['hpwl_delta'] and delta<=0;rows.append(dict(case=Path(path).parent.name,block_ids=sel['block_ids'],hpwl_delta=delta,touched_NETs=len(touch)))
assert all(sha(p)==h for p,h in bindings.items())
with (D/'geometry_independent_verification_v1.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all_pairs_disjoint_and_exclude_prior_pair=True,all_swaps_independent_from_original=True,hpwl_and_touched_NETs_independently_recomputed=True,scope='Membership and geometry arithmetic audit; ascending first-eligible selection follows bound producer, not independently re-enumerated. Physical placement legality and endpoints require subsequent native/XML checks; no routing or quality claim.'),f,indent=2)
print('PASS independent cohort geometry',rows,flush=True)
