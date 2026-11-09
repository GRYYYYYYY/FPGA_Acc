"""Recompute envelope directly from original per-node vectors, not source journals."""
import sys,json,array
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 d=R/'experiments/mmc_group_mass_envelope_v1_2026-10-18';p=d/'diagnosis.json';r=json.loads(p.read_text());gp=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18/groups.json';g=json.loads(gp.read_text());inverse={n:i for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel' for n in v['members']};prior=R/'experiments/mmc_pressure_risk_matrix_v1_2026-10-18';manifest=json.loads((prior/'vector_manifest.json').read_text());nodes=json.loads((prior/'domains.json').read_text())['ids']['channels'];assert set(nodes)==set(inverse);admitted=json.loads((R/'experiments/mmc_typed_risk_matrix_verification_v1_2026-10-18/verification.json').read_text());intervals=json.loads((d/'group_intervals.json').read_text());assert sha(d/'group_intervals.json')==r['group_intervals_sha256'];count=0
 for row in r['rows']:
  sources=[]
  for name in row['single_source_group_floors']:
   desc=manifest[row['case']+'__'+name+'__channels'];assert sha(desc['path'])==desc['sha256']==admitted['bindings'][desc['path']];a=array.array('d');a.frombytes(Path(desc['path']).read_bytes());mass={i:0 for i in set(inverse.values())}
   for n,v in zip(nodes,a):assert v==int(v);mass[inverse[n]]+=int(v)
   sources.append(mass)
  truth=json.loads((R/f'experiments/mmc_multiplacement_quality_v1_2026-10-18/{row["case"]}/vectors.json').read_text())['channels'];target={i:0 for i in sources[0]}
  for n in truth:target[inverse[n['node']]]+=n['labels']['cold']
  total=0
  for item in intervals[row['case']]:
   gid=item['group'];low=min(v[gid] for v in sources);high=max(v[gid] for v in sources);t=target[gid];distance=(low-t if t<low else t-high if t>high else 0);assert item==dict(group=gid,minimum_source_mass=low,maximum_source_mass=high,cold_mass=t,envelope_distance=distance);total+=distance;count+=1
  assert total==row['optimistic_mixture_L1_floor']
 for path,h in r['bindings'].items():assert sha(path)==h
 receipt=dict(status='all89496_group_intervals_verified_from_original_node_vectors',bindings={str(x):sha(x) for x in [p,Path(__file__),d/'group_intervals.json']},groups_verified=count,decision='Do not pursue convex source reweighting alone as a solution to inter-group mass mismatch. New topology-valid path support or source-independent group-mass information is required to remove this bound. This lower bound does not prove any original rank/utility gate impossible and is not a legal-routing impossibility certificate.')
 assert count==89496
 with (d/'verification_v1.json').open('x') as f:json.dump(receipt,f,indent=2)
 print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
