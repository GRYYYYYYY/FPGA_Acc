"""Independent all-plane bitset separators, identity transfer and capacity sums."""
import json,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def canonical(e):return (e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(canonical(c) for c in e))
def sig(e):
 l=e.find('loc');return (e.get('type'),int(e.get('capacity')),*(int(l.get(k,'0')) for k in ['xlow','ylow','xhigh','yhigh','layer','ptc']))
def bits(a,b):return ((1<<(b-a))-1)<<a if a<b else 0

def main():
 start=time.perf_counter();folder=Path(sys.argv[1]).resolve();pp=folder/'profiles.json';p=json.loads(pp.read_text());assert p['status']=='real_RR_separator_profiles_complete_independent_literal_review_pending';assert all(sha(k)==h for k,h in p['bindings'].items());spec=R/'experiments/width_stress_RR_separator_protocol_v1_2026-10-18/protocol.json';s=json.loads(spec.read_text());source=s['approved_prior_physical_NET_identity'][p['design']];approved_path=Path(source['approved_endpoints']);old=json.loads(approved_path.read_text());epfile=folder/'endpoints.json';ep=json.loads(epfile.read_text());scopefile=Path(ep['inputs']['original_CID_partition']['path']);partition=json.loads(scopefile.read_text());scopeproof=Path(source['whole_NET_ignore_partition']);v=json.loads(scopeproof.read_text());assert v['exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass'];assert v['bindings'][str(scopefile)]==sha(scopefile);assert all(sha(k)==h for k,h in v['bindings'].items());raw=json.loads(Path(ep['inputs']['all_endpoints']['path']).read_text());rawby={q['connection_id']:q for q in raw['connections']};before={q['connection_id']:q for q in old['connections']};after={q['connection_id']:q for q in ep['connections']};mapping={x['physical_connection_id']:x['original_connection_id'] for x in partition['physical_to_original_connection_ids']};assert set(before)==set(after)==set(mapping) and len(set(mapping.values()))==len(mapping);assert len(rawby)==v['all_queries'];ignored={x['original_query']['connection_id'] for x in partition['native_ignored_queries']};assert set(mapping.values()).isdisjoint(ignored) and set(mapping.values())|ignored==set(rawby)
 for cid,q in after.items():assert q==dict(rawby[mapping[cid]],connection_id=cid);assert ep['net_names'][str(q['net_id'])]==old['net_names'][str(before[cid]['net_id'])]
 for kind in ['net','place']:assert sha(ep['inputs'][kind]['path'])==ep['inputs'][kind]['sha256']==old['inputs'][kind]['sha256']
 graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];wanted={q[k] for q in after.values() for k in ['source','sink']};oldwanted={q[k] for q in before.values() for k in ['source','sink']};oldgraph=Path(old['inputs']['graph']['path']);assert sha(oldgraph)==old['graph_sha256'];oldsignatures={};oldblocks=oldgrid=None;stack=[]
 for event,e in ET.iterparse(oldgraph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='block_types':oldblocks=canonical(e)
  elif e.tag=='grid':oldgrid=tuple(sorted(tuple(sorted(x.attrib.items())) for x in e))
  elif e.tag=='node' and parent=='rr_nodes':
   n=int(e.get('id'))
   if n in oldwanted:oldsignatures[n]=sig(e)
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert set(oldsignatures)==oldwanted and oldblocks is not None and oldgrid is not None
 low={a:array('I') for a in ['x','y']};high={a:array('I') for a in ['x','y']};masks={a:[] for a in ['x','y']};caps=array('I');current_signatures={};seen_endpoint_signatures=set();edge_count=0;stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='block_types':assert canonical(e)==oldblocks
  elif e.tag=='grid':assert tuple(sorted(tuple(sorted(x.attrib.items())) for x in e))==oldgrid
  elif e.tag=='node' and parent=='rr_nodes':
   n=int(e.get('id'));assert n==len(caps);caps.append(int(e.get('capacity')));l=e.find('loc')
   for axis in ['x','y']:
    a,b=int(l.get(axis+'low')),int(l.get(axis+'high'));assert 0<=a<=b;low[axis].append(a);high[axis].append(b);masks[axis].append(bits(a,b))
   if e.get('type') in ['SOURCE','SINK']:
    signature=sig(e);assert signature not in seen_endpoint_signatures;seen_endpoint_signatures.add(signature)
   if n in wanted:current_signatures[n]=sig(e)
  elif e.tag=='edge' and parent=='rr_edges':
   u,v=int(e.get('src_node')),int(e.get('sink_node'));assert 0<=u<len(caps) and 0<=v<len(caps);edge_count+=1
   # Literal original-bbox crossing cuts: patch the actual directed destination.
   for axis in ['x','y']:
    if high[axis][u]<low[axis][v]:masks[axis][v]|=bits(high[axis][u],low[axis][v])
    elif high[axis][v]<low[axis][u]:masks[axis][v]|=bits(high[axis][v],low[axis][u])
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(caps)==p['RR_nodes'] and edge_count==p['RR_edges'];assert set(current_signatures)==wanted
 for cid,q in after.items():
  for role in ['source','sink']:assert current_signatures[q[role]]==oldsignatures[before[cid][role]]
 terminals=defaultdict(set);drivers=defaultdict(set)
 for q in after.values():terminals[q['net_id']].update([q['source'],q['sink']]);drivers[q['net_id']].add(q['source'])
 assert all(len(x)==1 for x in drivers.values()) and len(terminals)==p['physical_NETs'];reports={};all_planes=0;node_checks=0
 for axis in ['x','y']:
  lower=array('I');lower.frombytes((folder/f'{axis}_lower.u32').read_bytes());upper=array('I');upper.frombytes((folder/f'{axis}_upper.u32').read_bytes());assert p['array_byteorder']==sys.byteorder and len(lower)==len(upper)==len(caps);extent=max(high[axis]);capacity=[0]*extent;demand=[0]*extent
  for n,mask in enumerate(masks[axis]):
   assert mask==bits(lower[n],upper[n]);node_checks+=1;t=mask
   while t:
    bit=t&-t;k=bit.bit_length()-1;assert k<extent;capacity[k]+=caps[n];t^=bit
  intervals=json.loads((folder/f'{axis}_NET_intervals.json').read_text());assert set(map(int,intervals))==set(terminals)
  for net,ts in terminals.items():
   forced=bits(min(low[axis][n] for n in ts),max(high[axis][n] for n in ts))
   for n in ts:forced|=masks[axis][n]
   a,b=intervals[str(net)];assert forced==bits(a,b)
   while forced:
    bit=forced&-forced;k=bit.bit_length()-1;demand[k]+=1;forced^=bit
  rows=p['profiles'][axis]['cuts'];assert [r['cut_after_coordinate'] for r in rows]==sorted({r['cut_after_coordinate'] for r in rows});index=0;positive=[]
  for k in range(min(low[axis]),extent):
   while index+1<len(rows) and rows[index+1]['cut_after_coordinate']<=k:index+=1
   row=rows[index];assert row['cut_after_coordinate']<=k and row['separator_capacity']==capacity[k] and row['mandatory_unique_NETs']==demand[k] and row['excess']==demand[k]-capacity[k];all_planes+=1
   if demand[k]>capacity[k]:positive.append(dict(cut_after_coordinate=k,capacity=capacity[k],mandatory_NETs=demand[k],excess=demand[k]-capacity[k]))
  assert bool(positive)==p['profiles'][axis]['any_capacity_infeasibility_certificate_pending_independent_review'];reports[axis]=dict(integer_planes_verified=max(0,extent-min(low[axis])),positive_capacity_certificates=positive)
 bindings={**p['bindings'],str(pp):sha(pp),str(Path(__file__).resolve()):sha(Path(__file__).resolve()),str(oldgraph):sha(oldgraph),str(approved_path):sha(approved_path),str(scopeproof):sha(scopeproof)};assert all(sha(k)==h for k,h in bindings.items());positive=any(x['positive_capacity_certificates'] for x in reports.values());result=dict(status='independent_all_real_RR_plane_memberships_demands_capacities_and_endpoint_identity_pass',bindings=bindings,name=p['name'],all_original_RR_edges_used_for_literal_crossing_patch=True,block_types_grid_and_all_SOURCE_SINK_class_identities_equal_same_NET_place_archive=True,physical_queries=len(after),physical_NETs=len(terminals),node_plane_mask_checks=node_checks,integer_planes_verified=all_planes,profiles=reports,capacity_bound_result='CONDITIONAL_CAPACITY_INFEASIBILITY_CERTIFICATE' if positive else 'UNKNOWN_NO_POSITIVE_CAPACITY_BOUND',native_outcome_consumed=False,strict_unseen_family=False,seconds=time.perf_counter()-start,scope='Exact necessary capacity bounds for the supplied graph and authenticated same-input nonignored NET model. Nonpositive bound is UNKNOWN. This is not a native-policy result, sufficiency proof, congestion-quality/native utility or gain claim.');(folder/'independent_literal_verification_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print('ALL_REAL_RR_SEPARATOR_PLANES_VERIFIED',p['name'],len(after),all_planes,result['capacity_bound_result'],flush=True)
if __name__=='__main__':main()
