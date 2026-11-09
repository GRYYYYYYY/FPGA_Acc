"""Determine whether admitted IPIN mean/collision priors need routed paths."""
import json,sys
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 root=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18';proof=R/'experiments/mmc_typed_collision_risk_verification_v1_2026-10-18/verification.json';v=json.loads(proof.read_text());assert v['status']=='pass'
 config=json.loads((root/'protocol.json').read_text());group_path=root/'groups.json';assert sha(group_path)==v['bindings'][str(group_path)];groups=json.loads(group_path.read_text())['groups']
 geometry=R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json';previous_endpoint=Path(json.loads(geometry.read_text())['previous_endpoint'])
 bindings={str(proof):sha(proof),str(group_path):sha(group_path),str(geometry):sha(geometry),**closure([Path(__file__)])};cache={};rows=[]
 def owners(path):
  key=str(path)
  if key not in cache:
   assert v['bindings'][key]==sha(path);bindings[key]=sha(path);ep=json.loads(path.read_text());result=defaultdict(set)
   for q in ep['connections']:result[q['sink']].add(q['net_id'])
   cache[key]=result
  return cache[key]
 old=owners(previous_endpoint)
 for case in ['case_01','case_02','case_03']:
  current=owners(Path(config['inputs'][case]['endpoint']));counts_changed=sum(len(old.get(sink,()))!=len(current.get(sink,())) for sink in set(old)|set(current))
  memberships_changed=sum(len(old.get(sink,set())^current.get(sink,set())) for sink in set(old)|set(current))
  for method in config['methods']:
   path=root/(case+'__'+method+'.json');assert v['bindings'][str(path)]==sha(path);bindings[str(path)]=sha(path);journal=json.loads(path.read_text());active=journal['positive_group_histograms'];source=old if method=='previous_native' else current;classes=0;pins=0
   for gid,g in enumerate(groups):
    if g['kind']!='direct_sink_IPIN':continue
    q=len(source.get(g['sink_RR'],()));m=len(g['members']);stored=active.get(str(gid));hist={int(k):count for k,count in stored['NET_occupancy_histogram'].items()} if stored else {}
    assert hist==({1:q} if q else {})
    mean=Fraction(q,m);empty=Fraction(m-1,m)**q;collision=mean-1+empty
    if stored:assert Fraction(stored['expected_occupancy'])==mean and Fraction(stored['expected_overflow'])==collision and Fraction(stored['probability_empty'])==empty
    else:assert mean==collision==0 and empty==1
    classes+=1;pins+=m
   rows.append(dict(case=case,source=method,IPIN_classes_checked=classes,IPIN_nodes_checked=pins,mean_and_collision_priors_exact_from_endpoint_NET_sets=True,current_vs_previous_classes_with_changed_NET_count=counts_changed,current_vs_previous_NET_class_membership_symmetric_difference=memberships_changed))
 out=R/'experiments/mmc_IPIN_endpoint_sufficiency_v1_2026-10-18';out.mkdir()
 with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,rows=rows,unique_endpoint_snapshots_read=len(cache),IPIN_prior_values_transferred_from_full_vector_proof=sum(r['IPIN_nodes_checked']*2 for r in rows),scope='Only admitted unit direct-SINK IPIN group mean/collision components, all18sources. Reconstructed from distinct NETs per sink class without reading routed frame paths. Channel priors and observed-overflow pin assignments are not reconstructed. This is feature sufficiency, not runtime/end-to-end or predictive gain.'),stream,indent=2)
 print(json.dumps(dict(status='pass',source_states=len(rows),endpoint_snapshots=len(cache),IPIN_mean_collision_values=sum(r['IPIN_nodes_checked']*2 for r in rows))),flush=True)

if __name__=='__main__':main()
