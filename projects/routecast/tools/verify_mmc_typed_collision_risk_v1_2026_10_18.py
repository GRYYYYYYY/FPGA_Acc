"""Independent inverse NET ownership and exact polynomial expectation replay."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict,Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 root=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18';receipt=root/'receipt.json';v=json.loads(receipt.read_text());assert v['status']=='all54_source_only_type_consistent_risk_vectors_materialized'
 config=json.loads((root/'protocol.json').read_text());inventory=json.loads((root/'groups.json').read_text());groups=inventory['groups'];manifest=json.loads((root/'vector_manifest.json').read_text())
 bindings={**v['bindings'],str(receipt):sha(receipt),**closure([Path(__file__)])}
 out=R/'experiments/mmc_typed_collision_risk_verification_v1_2026-10-18';out.mkdir();cache=Cache();summaries=[];seen_vectors=set()
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  ep=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==inventory['graph_sha256']
  caps=[];types=[];destinations=array('I');outdegree=Counter();successors=defaultdict(set);stack=[]
  for action,e in ET.iterparse(graph,events=('start','end')):
   if action=='start':stack.append(e.tag);continue
   parent=stack[-2] if len(stack)>1 else None
   if e.tag=='node' and parent=='rr_nodes':
    assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));types.append(e.get('type'));e.clear()
   if e.tag=='edge' and parent=='rr_edges':
    u,w=int(e.get('src_node')),int(e.get('sink_node'));destinations.append(w);outdegree[u]+=1
    if types[u]=='IPIN':successors[u].add(w)
    e.clear()
   stack.pop()
  positive=[n for n,cap in enumerate(caps) if cap>0];assert positive==inventory['positive_RR_ids'] and len(destinations)==8097539
  pool=defaultdict(list)
  for n in positive:
   if types[n]=='IPIN' and len(successors[n])==1:
    sink=next(iter(successors[n]))
    if types[sink]=='SINK' and caps[sink]>0 and outdegree[sink]==0:pool[sink].append(n)
  expected_ipin={sink:members for sink,members in pool.items() if all(caps[n]==1 for n in members)}
  assert {g['sink_RR']:g['members'] for g in groups if g['kind']=='direct_sink_IPIN'}==expected_ipin
  old=json.loads((R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18/groups.json').read_text())
  assert [(g['geometry_key'],g['members']) for g in groups if g['kind']=='geometry_channel']==[(g['key'],[n for n,cap in g['members']]) for g in old['groups']]
  group_of={}
  for i,g in enumerate(groups):
   assert len(g['members'])==len(set(g['members'])) and all(caps[n]==1 for n in g['members'])
   for n in g['members']:assert n not in group_of;group_of[n]=i
  fallbacks={int(n):reason for n,reason in inventory['fallback_reasons'].items()}
  assert set(positive)==set(group_of)|set(fallbacks) and set(group_of).isdisjoint(fallbacks)
  for n,reason in fallbacks.items():
   if types[n]=='IPIN':assert reason in ['IPIN_not_single_terminal_SINK_pool','IPIN_pool_nonunit_capacity']
   else:assert reason=='fixed_or_unsupported_type_'+types[n]
  assert inventory['byteorder']==sys.byteorder and inventory['array_type']=='double' and inventory['array_itemsize']==8
  for case in ['case_01','case_02','case_03']:
   active=0;multi_node_NET_groups=0
   for method in config['methods']:
    path=Path(config['inputs'][case]['predictions'][method]);frame=json.loads(path.read_text());data=json.loads((root/(case+'__'+method+'.json')).read_text());assert sha(path)==data['source_frame_sha256'] and data['groups_sha256']==sha(root/'groups.json')
    node_owners=defaultdict(set)
    for r in frame['records']:
     node_owners[r['source']].add(r['net_id'])
     for edge in r['answer']['physical_edge_ids']:node_owners[destinations[edge]].add(r['net_id'])
    assert {n:len(owners) for n,owners in node_owners.items()}=={int(n):value for n,value in frame['ledger'].items() if value}
    per_group=defaultdict(Counter)
    for n,owners in node_owners.items():
     if n in group_of:
      for net in owners:per_group[group_of[n]][net]+=1
    journal={int(gid):row for gid,row in data['positive_group_histograms'].items()};assert set(journal)==set(per_group)
    expectation={}
    for gid,net_counts in per_group.items():
     size=len(groups[gid]['members']);ks=list(net_counts.values());assert all(1<=k<=size for k in ks)
     # Integer generating polynomial: factors (m-k)+k*z. Unlike producer,
     # retain every occupancy coefficient, including overflow multiplicities.
     coefficients=[1]
     for k in ks:
      following=[0]*(len(coefficients)+1)
      for load,count in enumerate(coefficients):following[load]+=count*(size-k);following[load+1]+=count*k
      coefficients=following
     denominator=size**len(ks);assert sum(coefficients)==denominator
     mean=Fraction(sum(load*count for load,count in enumerate(coefficients)),denominator)
     pressure=Fraction(sum(max(0,load-1)*count for load,count in enumerate(coefficients)),denominator)
     empty=Fraction(coefficients[0],denominator);row=journal[gid]
     assert {int(k):count for k,count in row['NET_occupancy_histogram'].items()}==dict(Counter(ks))
     assert Fraction(row['expected_occupancy'])==mean and Fraction(row['expected_overflow'])==pressure and Fraction(row['probability_empty'])==empty
     assert mean*size==sum(len(node_owners.get(n,())) for n in groups[gid]['members'])
     expectation[gid]=(mean,pressure);multi_node_NET_groups+=sum(k>1 for k in ks)
    for family in ['observed_overflow','typed_group_mean','typed_NET_collision']:
     name=case+'__'+method+'__'+family;info=manifest[name];assert data['vectors'][family]==info
     path=Path(info['path']);assert sha(path)==info['sha256'] and path.stat().st_size==len(positive)*8
     values=array('d');values.frombytes(path.read_bytes());assert len(values)==len(positive)==info['values']
     for index,n in enumerate(positive):
      expected=Fraction(max(0,len(node_owners.get(n,()))-caps[n]),caps[n])
      if family!='observed_overflow' and n in group_of:expected=expectation.get(group_of[n],(Fraction(0),Fraction(0)))[0 if family=='typed_group_mean' else 1]
      assert values[index]==float(expected),(case,method,family,n)
     bindings[str(path)]=info['sha256'];seen_vectors.add(name)
    active+=len(per_group);print('TYPED SOURCE REPLAY PASS',case,method,flush=True)
   summaries.append(dict(case=case,source_states_verified=6,vectors_verified=18,active_group_polynomials_verified=active,multi_resource_same_NET_group_memberships=multi_node_NET_groups))
  assert len(seen_vectors)==54 and seen_vectors==set(manifest) and all(sha(path)==h for path,h in bindings.items())
  with (out/'verification.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,summaries=summaries,groups=len(groups),IPIN_groups=len(expected_ipin),positive_RR_nodes=len(positive),all54_vectors_independently_rebuilt=True,scope='OriginalXML IPIN pool construction and complete domains, inverse node->NET ownership, full integer occupancy polynomials and all binary scores. Existing independently admitted channel partition transferred by exact inventory equality. Proves declared prior implementation only, not native reachability/dynamics, prediction improvement or primary gate success.'),stream,indent=2)

if __name__=='__main__':main()
