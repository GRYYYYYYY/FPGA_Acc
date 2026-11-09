"""Reconstruct every borrowed compiled-tree observation from admitted path prefixes."""
import array,collections,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';root=E/'mmc_borrowed_initializer_probe_v2_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());assert len(r['rows'])==3;oldp=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';old={q['connection_id']:q for q in json.loads(oldp.read_text())['records']};assert sha(oldp)==r['bindings'][str(oldp)];idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());gp=E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json';gvp=gp.parent/'independent_verification_v1.json';gpdata=json.loads(gp.read_text());gverify=json.loads(gvp.read_text());assert sha(gp)==gverify['bindings'][str(gp)] and sha(idxp)==gpdata['bindings'][str(idxp)];edges=[]
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==gpdata['bindings'][d['path']];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());edges.append(a)
 # Removing only observation additions must restore the exact original policy source.
 baselinep=R/'tools/native_retained_net_initializer_v1.py';observedp=R/'tools/native_retained_net_initializer_observed_v2.py';text=observedp.read_text();text=text.replace('from types import MappingProxyType\n\nclass Rejected(ValueError):pass\nclass ObservationError(RuntimeError):pass','class Rejected(ValueError):pass').replace('edge_slots,fallback,*,frontier_probe=None,emit=None):','edge_slots,fallback):');text=text.replace(" if (frontier_probe is None)!=(emit is None) or (emit is not None and not callable(emit)):raise ValueError('probe and callable observer must be supplied together')\n",'');begin=text.index(' def observe(');end=text.index(' eligible=sorted(',begin);text=text[:begin]+text[end:];text=text.replace("   repair_calls+=1;observe('before_expand',cid,tree);result=expand(tree,qs[cid]['sink'],budgets[cid]);observe('after_expand',cid,tree,result)","   repair_calls+=1;result=expand(tree,qs[cid]['sink'],budgets[cid])");assert text==baselinep.read_text();oldcorep=E/'native_retained_initializer_core_v3_2026-10-18/verification.json';oldcore=json.loads(oldcorep.read_text());assert sha(baselinep)==oldcore['sources'][str(baselinep)]
 def nodes(q,answer):
  u=q['source'];seen={u}
  for edge in answer['physical_edge_ids']:assert edges[0][edge]==u;u=edges[1][edge];assert u not in seen;seen.add(u)
  assert u==q['sink'];return seen
 data=[];needed=set()
 for row in r['rows']:
  case=row['case'];framep=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/native_retained/initial.json';assert sha(framep)==r['bindings'][str(framep)];frame=json.loads(framep.read_text());expected={q['connection_id']:q for q in frame['records']};assert set(expected)==set(old)==set(range(115572));assert sha(row['results']['baseline']['path'])==sha(row['results']['observed']['path'])==row['results']['baseline']['sha256']==row['results']['observed']['sha256'];returns=json.loads(Path(row['results']['observed']['path']).read_text());assert len(returns)==row['dirty_NETs'] and all(not x['result']['whole_NET_fallback'] for x in returns);assert sha(row['observation_file'])==row['observation_sha256'];observations=[json.loads(s) for s in Path(row['observation_file']).read_text().splitlines()];groups=collections.defaultdict(list)
  for c,q in expected.items():groups[q['net_id']].append(c)
  union={}
  for entry in returns:
   net=entry['net_id'];result=entry['result'];answers={int(c):a for c,a in result['answers'].items()};assert set(answers)==set(groups[net]);eligible=sorted(c for c in groups[net] if (old[c]['source'],old[c]['sink'])==(expected[c]['source'],expected[c]['sink']));assert eligible==result['retained_connection_ids']==result['attempted_retained_connection_ids'];members={}
   for c,a in answers.items():assert a==expected[c]['answer'];members[c]=nodes(expected[c],a);needed.update(members[c])
   for c in eligible:assert answers[c]==old[c]['answer']
   assert set().union(*members.values())==set(result['owner_nodes']);union[net]=(members,eligible)
  # Complete source/updated answer identity, not just repaired paths.
  updates={int(c):a for x in returns for c,a in x['result']['answers'].items()}
  for c in old:assert updates.get(c,old[c]['answer'])==expected[c]['answer']
  data.append((row,expected,returns,observations,groups,union))
 graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)==idx['graph_sha256']==r['bindings'][str(graph)];geo={};stack=[]
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   node=int(n.get('id'))
   if node in needed:
    loc=n.find('loc');geo[node]=(n.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')))
   parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert set(geo)==needed;checked=0;rows=[]
 for row,expected,returns,observations,groups,union in data:
  cursor=0
  for entry in returns:
   net=entry['net_id'];members,eligible=union[net];source=expected[groups[net][0]]['source'];tree={source}
   for c in eligible:tree.update(members[c])
   for c in sorted(set(groups[net])-set(eligible)):
    target=expected[c]['sink'];b=geo[target]
    for phase in ['before_expand','after_expand']:
     if phase=='after_expand':tree.update(members[c])
     event=observations[cursor];cursor+=1;assert event['phase']==phase and event['connection_id']==c and event['net_id']==net and event['source']==source and event['target']==target and event['graph_epoch']==idx['graph_sha256'];actual=[];projected=[];expand_count=0
     for n in tree:
      a=geo[n];expandable=a[0] in ['SOURCE','OPIN','CHANX','CHANY'];expand_count+=expandable
      if a[5]!=b[5]:continue
      x=b[1]-a[2] if a[2]<b[1] else a[1]-b[2] if b[2]<a[1] else 0;y=b[3]-a[4] if a[4]<b[3] else a[3]-b[4] if b[4]<a[3] else 0;actual.append(x+y)
      if expandable:projected.append(x+y)
     assert event['actual_seed_nodes']==len(tree) and event['actual_same_layer_nodes']==len(actual) and event['actual_min_tile_L1']==(min(actual) if actual else None) and event['projected_expandable_nodes']==expand_count and event['projected_same_layer_nodes']==len(projected) and event['projected_min_tile_L1']==(min(projected) if projected else None)
     if phase=='after_expand':assert event['expand_committed'] is True and event['expand_status']=='COMMITTED'
     checked+=1
  assert cursor==len(observations)==row['observations'];rows.append(dict(case=row['case'],dirty_NETs=row['dirty_NETs'],observations_reconstructed=cursor,complete_CID_answers_verified=115572));print('INDEPENDENT BORROWED TREE OBSERVATIONS PASS',row['case'],cursor,flush=True)
 assert checked==566
 for p,h in r['bindings'].items():assert sha(p)==h
 bindings={str(p):sha(p) for p in [rp,Path(__file__),gp,gvp,idxp,oldcorep]}
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all566_borrowed_tree_observations_and_initializer_policy_parity_independently_verified',bindings=bindings,rows=rows,observation_records_verified=checked,original_policy_source_recovered_exactly_by_removing_observer=True,scope='Real cases have no wholeNET fallbacks, so prefix trees reconstruct from retained siblings and prior successful answers. Fallback/error behavior separately covered by core fixtures. No extra NET state index, native seed equivalence, new policy, heldout validation or complete-time gain certified.'),f,indent=2)
if __name__=='__main__':main()
