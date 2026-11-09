"""Inverse node-owner verification, without producer NET-union traversal."""
import sys,json,array,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';d=E/'mmc_per_NET_footprint_envelope_v1_2026-10-18';rp=d/'diagnosis.json';r=json.loads(rp.read_text());config=json.loads((E/'mmc_typed_collision_risk_v1_2026-10-18/protocol.json').read_text());g=json.loads((E/'mmc_typed_collision_risk_v1_2026-10-18/groups.json').read_text());inverse={n:i for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel' for n in v['members']};index=json.loads((E/'real_joint_full_score_v2_2026-10-18/graph_index.json').read_text());dest=array.array('I');dest.frombytes(Path(index['arrays']['edge_destination']['path']).read_bytes());sources=[s for s in config['methods'] if s!='previous_native'];assert len(sources)==5;count=0
 for row in r['rows']:
  pairvalues={}
  for si,source in enumerate(sources):
   f=json.loads(Path(config['inputs'][row['case']]['predictions'][source]).read_text());owners=collections.defaultdict(set)
   for record in f['records']:
    owners[record['source']].add(record['net_id'])
    for edge in record['answer']['physical_edge_ids']:owners[dest[edge]].add(record['net_id'])
   paircounts=collections.Counter()
   for node,nets in owners.items():
    if node in inverse:
     for net in nets:paircounts[inverse[node],net]+=1
   for pair,k in paircounts.items():pairvalues.setdefault(pair,[0]*5)[si]=k
  low=collections.Counter();high=collections.Counter()
  for (gid,net),values in pairvalues.items():low[gid]+=min(values);high[gid]+=max(values)
  ip=Path(row['intervals']);assert sha(ip)==row['sha256'];items=json.loads(ip.read_text());floor=outside=0
  for v in items:
   gid=v['group'];assert v['minimum_per_NET_mass']==low[gid] and v['maximum_per_NET_mass']==high[gid];distance=max(low[gid]-v['cold_mass'],v['cold_mass']-high[gid],0);assert distance==v['distance'];floor+=distance;outside+=distance>0;count+=1
  assert floor==row['per_NET_envelope_L1_floor'] and outside==row['outside_per_NET_envelope']
 for path,h in r['bindings'].items():assert sha(path)==h
 review=dict(status='all89496_per_NET_footprint_intervals_independently_verified',bindings={str(p):sha(p) for p in [rp,Path(__file__)]},groups_verified=count,decision='Do not use current-footprint source selection alone to resolve group-mass mismatch. Remaining mechanism must introduce new endpoint-compatible path support or independently validated inter-group prediction; no tuning/fitting on these cold labels. Bounds remain optimistic and do not prove legal routing infeasibility or original rank-gate impossibility.')
 assert count==89496
 with (d/'verification_v1.json').open('x') as f:json.dump(review,f,indent=2)
 print(json.dumps(review,indent=2),flush=True)
if __name__=='__main__':main()
