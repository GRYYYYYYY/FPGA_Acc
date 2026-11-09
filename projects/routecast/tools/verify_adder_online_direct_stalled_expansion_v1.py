"""Authenticate unchanged candidate banks and duplicate successful owner searches."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_online_direct_stalled_expansion_verification_v1_2026-10-09';D.mkdir(exist_ok=False);bindings=closure([Path(__file__)])
def doc(directory,name):
 p=E/directory/name;d=json.loads(p.read_text());bindings[str(p)]=sha(p)
 if 'bindings' in d:
  assert all(sha(p)==h for p,h in d['bindings'].items());bindings.update(d['bindings'])
 return d
old='adder_online_direct_leaf_owner_expand_v1_2026-10-09';prior=doc(old,'step_3.json')['bank'];proof=doc('adder_online_direct_leaf_owner_component_verification_v1_2026-10-09','verification.json');assert len(proof['rows'][0]['dead_leaves'])==6
rows=[]
for directory in ['adder_online_direct_net_release_search_v1_2026-10-09','adder_online_direct_leaf_owner_expand_v2_2026-10-09']:
 report=doc(directory,'verification.json');data=doc(directory,'step_3.json');assert data['bank']==prior and report['rows'][0]['new_candidates']==0
 assert len(data['attempts'])==6 and all(x['status']=='NO_STRICT_IMPROVEMENT' for x in data['attempts'])
 owners=data.get('owner_attempts',[])
 for event in owners:
  assert event['status']=='FOUND' and any(o['path']==event['path'] for o in prior[str(event['connection_id'])]);assert not set(event['forbidden_nodes'])&{n for n,s in event['path']}
 rows.append(dict(experiment=directory,background_queries=6,new_candidates=0,owner_queries=len(owners),all_found_owner_paths_already_in_verified_bank=True))
assert rows[1]['owner_queries']==8
for directory in ['adder_online_direct_net_release_components_v1_2026-10-09','adder_online_direct_leaf_owner_components_v2_2026-10-09']:
 result=doc(directory,'verification.json');assert result['status']=='FINITE_BANK_EXHAUSTED';current=doc(directory,'component_1.json');original=doc('adder_online_direct_leaf_owner_components_v1_2026-10-09','component_1.json');assert current==original
 assert doc(directory,'propagation.json')==doc('adder_online_direct_leaf_owner_components_v1_2026-10-09','propagation.json');assert doc(directory,'decomposition.json')==doc('adder_online_direct_leaf_owner_components_v1_2026-10-09','decomposition.json')
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,unchanged_independently_certified_finite_bank_proof=True,scope='No-new-candidate outcomes authenticated; exact banks/domains/decomposition/proof unchanged from independently verified 813-candidate experiment. NO_STRICT_IMPROVEMENT is not global physical infeasibility. No new native or performance claim.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
