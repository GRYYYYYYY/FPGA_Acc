"""Inverse resource-owner reconstruction and independent exact support bounds."""
import array,collections,itertools,json,sys,xml.etree.ElementTree as ET
from fractions import Fraction as F
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';root=E/'mmc_local_feedback_support_v1_2026-10-18';rp=root/'results.json';r=json.loads(rp.read_text());tm=json.loads((root/'vector_manifest.json').read_text());idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());a=[]
 for name in ['edge_source','edge_destination','positive_capacity']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==r['bindings'][d['path']];v=array.array('I');v.frombytes(Path(d['path']).read_bytes());a.append(v)
 sourcep=E/'mmc_native_source_checkpoint_v1_2026-10-18/initial.json';old={q['connection_id']:q for q in json.loads(sourcep.read_text())['records']};inverse=collections.defaultdict(set)
 def project(q):
  node=q['source'];ns={node}
  for edge in q['answer']['physical_edge_ids']:assert a[0][edge]==node;node=a[1][edge];assert node not in ns;ns.add(node)
  assert node==q['sink'];return ns
 for q in old.values():
  for n in project(q):inverse[n].add(q['net_id'])
 cache={};data=[];channels=None;bins=None
 def read(desc):
  assert sha(desc['path'])==desc['sha256'];x=array.array('I');x.frombytes(Path(desc['path']).read_bytes());assert len(x)==desc['values'] and desc['byteorder']==sys.byteorder;return x
 for case in ['case_01','case_02','case_03']:
  model=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}';initial=json.loads((model/'native_retained/initial.json').read_text());ip={q['connection_id']:q for q in initial['records']};dirty={q['net_id'] for c,q in ip.items() if (q['source'],q['sink'])!=(old[c]['source'],old[c]['sink'])};current_owners=collections.defaultdict(set)
  for q in initial['records']:
   for n in project(q):current_owners[n].add(q['net_id'])
  overused={n for n,owners in current_owners.items() if len(owners)>a[2][n]};expanded=dirty|set().union(*(current_owners[n] for n in overused));masks=json.loads((root/case/'mutable_NETs.json').read_text());assert set(masks['endpoint_dirty'])==dirty and set(masks['dirty_plus_initial_overuse_owners'])==expanded
  # Every executed snapshot preserves unselected source paths and every round's schedule.
  frozen_cids=set(old)-{c for c,q in old.items() if q['net_id'] in dirty}
  for path in [model/'native_retained/initial.json',*[model/f'feedback_on/native_retained/round{i}.json' for i in range(2)],model/'feedback_on/native_retained/sketch.json']:
   state=json.loads(path.read_text());assert len(state['records'])==115572
   for q in state['records']:
    if q['connection_id'] in frozen_cids:
     expected=old[q['connection_id']];assert all(q[k]==expected[k] for k in ['net_id','source','sink','answer'])
  receipt=json.loads((model/'feedback_on/native_retained/receipt.json').read_text());assert all(set(x['affected_nets'])==dirty and {e['net_id'] for e in x['events']}==dirty for x in receipt['rounds'])
  vecp=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/vectors.json';vectors=json.loads(vecp.read_text());qproof=json.loads((vecp.parent/'verification.json').read_text());assert sha(vecp)==qproof['bindings'][str(vecp)];ch=vectors['channels'];bs=vectors['bins']
  if channels is None:channels=[x['node'] for x in ch];bins=[tuple(x['key']) for x in bs]
  assert channels==[x['node'] for x in ch] and bins==[tuple(x['key']) for x in bs]
  for mask in ['endpoint_dirty','dirty_plus_initial_overuse_owners']:
   mutable=set(masks[mask]);expected=array.array('I',[len(inverse[n]-mutable) for n in channels]);actual=read(tm[case+'__'+mask+'__channels']);assert actual==expected;binvalues=read(tm[case+'__'+mask+'__bins']);data.append(dict(case=case,mask=mask,channel_counts=expected,bin_counts=binvalues,expected_bins=array.array('I',[0])*len(bins),channels=ch,bins=bs,mutable_NETs=len(mutable),frozen_CIDs=len(frozen_cids)))
  print('INVERSE OWNERS AND ALL FROZEN SNAPSHOTS PASS',case,len(dirty),len(expanded),flush=True)
 node_index={n:i for i,n in enumerate(channels)};bin_index={k:i for i,k in enumerate(bins)};capacities=collections.Counter();seen=set();graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';stack=[]
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   if n.get('type') in ['CHANX','CHANY'] and int(n.get('capacity'))>0:
    node=int(n.get('id'));assert node in node_index and node not in seen;seen.add(node);loc=n.find('loc');seg=n.find('segment');sid=int(seg.get('segment_id')) if seg is not None else -1
    for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1):
     for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1):
      b=bin_index[int(loc.get('layer','0')),x,y,n.get('type'),sid];capacities[b]+=int(n.get('capacity'))
      for item in data:item['expected_bins'][b]+=item['channel_counts'][node_index[node]]
   parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert seen==set(channels) and len(bins)==17160;checked=0
 for item in data:
  assert item['bin_counts']==item['expected_bins'] and all(capacities[i]==v['capacity'] for i,v in enumerate(item['bins']))
  for domain,values,table in [('channels',item['channel_counts'],item['channels']),('bins',item['bin_counts'],item['bins'])]:
   row=next(x for x in r['rows'] if (x['case'],x['mask'],x['domain'])==(item['case'],item['mask'],domain));assert row['mutable_NETs']==item['mutable_NETs'] and row['current_endpoint_only_frozen_CIDs']==item['frozen_CIDs'];best_error=F(0);actual_error=F(0);over=F(0);forced=0
   for fixed,v in zip(values,table):
    truth=v['labels']['cold'];pred=v['predictions']['native_retained_on'];capacity=v['capacity'];best=max(fixed,truth);assert pred>=fixed;best_error+=F(abs(best-truth),capacity);actual_error+=F(abs(pred-truth),capacity);over+=F(max(0,pred-truth),capacity);forced+=fixed>truth
   best_error/=len(table);actual_error/=len(table);over/=len(table);assert F(row['optimistic_normalized_MAE_lower_bound'])==best_error and F(row['current_normalized_MAE'])==actual_error and row['coordinates_with_unavoidable_overprediction']==forced;assert row['lower_bound_share_of_current_MAE']==float(best_error/actual_error) and row['lower_bound_share_of_current_overprediction']==float(best_error/over);checked+=1
  print('EXACT POINT AND BIN LOWER BOUNDS PASS',item['case'],item['mask'],flush=True)
 assert checked==12
 for p,h in r['bindings'].items():assert sha(p)==h
 bindings={str(p):sha(p) for p in [rp,root/'protocol.json',root/'vector_manifest.json',Path(__file__)]}
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all12_fixed_support_bounds_inverse_owners_original_XML_bins_and_frozen_snapshots_verified',bindings=bindings,bound_cells_verified=checked,channel_mask_values_verified=6*258720,bin_mask_values_verified=6*17160,scope='Exact optimistic MAE lower bound for fixed unselected point-occupancy paths. Not a Spearman/TopK impossibility bound, uncertainty-prior bound or evidence that an expanded scheduling policy improves accepted routing or time.'),f,indent=2)
if __name__=='__main__':main()
