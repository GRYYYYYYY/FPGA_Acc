"""Per-NET existing-footprint envelope, deliberately optimistic about assembly legality."""
import sys,json,array,collections
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';cp=E/'mmc_typed_collision_risk_v1_2026-10-18/protocol.json';config=json.loads(cp.read_text());gp=E/'mmc_typed_collision_risk_v1_2026-10-18/groups.json';g=json.loads(gp.read_text());groups={i:v for i,v in enumerate(g['groups']) if v['kind']=='geometry_channel'};group_of={n:i for i,v in groups.items() for n in v['members']};pp=E/'mmc_anchored_NET_forecasts_verification_v1_2026-10-18/verification.json';proof=json.loads(pp.read_text());ip=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';index=json.loads(ip.read_text());arrays=[];bindings={str(p):sha(p) for p in [Path(__file__),cp,gp,pp,ip]}
 for key in ['edge_source','edge_destination']:
  desc=index['arrays'][key];assert sha(desc['path'])==desc['sha256'];a=array.array('I');a.frombytes(Path(desc['path']).read_bytes());arrays.append(a);bindings[desc['path']]=desc['sha256']
 starts,dest=arrays;sources=[s for s in config['methods'] if s!='previous_native'];assert len(sources)==5;out=E/'mmc_per_NET_footprint_envelope_v1_2026-10-18';out.mkdir(exist_ok=False);rows=[]
 (out/'protocol.json').write_text(json.dumps(dict(sources=sources,excluded='previous_native uses old-placement endpoints',scope='Retrospective optimistic per-NET footprint-choice envelope, no fitted weights or new predictions. Full per-NET/source path sets are retained as indivisible footprints; later group-wise envelope still relaxes joint group compatibility and native capacity/timing/tree legality.'),indent=2))
 for case,inputs in config['inputs'].items():
  ep=Path(inputs['endpoint']);endpoint=json.loads(ep.read_text());queries={r['connection_id']:r for r in endpoint['connections']};assert len(queries)==115572;bindings[str(ep)]=sha(ep);stats={};mass_by_source={};domain=None
  for source in sources:
   path=Path(inputs['predictions'][source]);assert sha(path)==proof['bindings'][str(path)];bindings[str(path)]=sha(path);frame=json.loads(path.read_text());owned=collections.defaultdict(set);seen=set()
   for r in frame['records']:
    q=queries[r['connection_id']];assert r['connection_id'] not in seen and all(r[k]==q[k] for k in ['net_id','source','sink']);seen.add(r['connection_id']);node=r['source'];owned[r['net_id']].add(node)
    for edge in r['answer']['physical_edge_ids']:
     assert starts[edge]==node;node=dest[edge];owned[r['net_id']].add(node)
    assert node==r['sink']
   assert seen==queries.keys();nets=set(owned)
   if domain is None:domain=nets
   assert nets==domain and len(nets)==55300;totals=collections.Counter()
   for net,nodes in owned.items():
    ks=collections.Counter(group_of[n] for n in nodes if n in group_of)
    for gid,k in ks.items():
     totals[gid]+=k;key=(gid,net)
     if key not in stats:stats[key]=[1,k,k]
     else:v=stats[key];v[0]+=1;v[1]=min(v[1],k);v[2]=max(v[2],k)
   mass_by_source[source]=totals;print('FOOTPRINT SUPPORT',case,source,len(stats),flush=True)
  low=collections.Counter();high=collections.Counter()
  for (gid,net),(seen,min_k,max_k) in stats.items():low[gid]+=min_k if seen==len(sources) else 0;high[gid]+=max_k
  vp=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/vectors.json';truth={r['node']:r['labels']['cold'] for r in json.loads(vp.read_text())['channels']};bindings[str(vp)]=sha(vp);records=[];floor=globalfloor=0;outside=globaloutside=0
  for gid,group in groups.items():
   target=sum(truth[n] for n in group['members']);lo,hi=low[gid],high[gid];oldlo=min(v[gid] for v in mass_by_source.values());oldhi=max(v[gid] for v in mass_by_source.values());assert lo<=oldlo<=oldhi<=hi;distance=max(lo-target,target-hi,0);floor+=distance;outside+=distance>0;old_distance=max(oldlo-target,target-oldhi,0);globalfloor+=old_distance;globaloutside+=old_distance>0;records.append(dict(group=gid,minimum_per_NET_mass=lo,maximum_per_NET_mass=hi,cold_mass=target,distance=distance))
  assert floor<=globalfloor;p=out/(case+'_intervals.json');p.write_text(json.dumps(records,separators=(',',':')));rows.append(dict(case=case,NETs=len(domain),groups=len(groups),group_NET_pairs=len(stats),outside_per_NET_envelope=outside,outside_global_source_envelope=globaloutside,per_NET_envelope_L1_floor=floor,global_source_envelope_L1_floor=globalfloor,per_NET_envelope_MAE_floor=floor/258720,intervals=str(p),sha256=sha(p)))
 for p,h in bindings.items():assert sha(p)==h
 with (out/'diagnosis.json').open('x') as f:json.dump(dict(status='all_three_endpoint_matched_per_NET_footprint_envelopes_computed',bindings=bindings,rows=rows,scope='Excludes stale previous_native. Checks all current source paths against exact current endpoints and admitted edge arrays. Per-NET footprint bounds do not guarantee one compatible whole-NET choice across groups, legal tree assembly, capacity, budget, native routing, forecast quality or unseen-family admission.'),f,indent=2)
 print(json.dumps(rows,indent=2),flush=True)
if __name__=='__main__':main()
