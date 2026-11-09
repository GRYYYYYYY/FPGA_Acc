"""Independent admitted path binding, real partial-batch rejection and direct update."""
import array,collections,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from retained_tree_frontier_state_v2 import Cache

def main():
 E=R/'experiments';root=E/'mmc_source_frontier_restore_real_v2_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());assert len(r['rows'])==3;proofp=E/'mmc_joint_channel_diamond_v1_2026-10-18/independent_full_frame_v1.json';proof=json.loads(proofp.read_text());idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());edges=[]
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==r['bindings'][d['path']];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());edges.append(a)
 data=[];needed=set()
 for row in r['rows']:
  case=row['case'];stagesp=Path(row['artifact']);assert sha(stagesp)==row['artifact_sha256'];stages=json.loads(stagesp.read_text());assert len(stages)==3 and [s['generation'] for s in stages]==[1,2,3];assert stages[0]['receipt']['removed_connections']==14 and stages[1]['receipt']['restored_connections']==14 and stages[1]['receipt']['replaced_connections']==0 and stages[2]['receipt']['replaced_connections']==14 and stages[2]['receipt']['restored_connections']==0;maps=[];used=set()
  for p in [E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/sketch.json',E/f'mmc_joint_channel_diamond_v1_2026-10-18/{case}/candidate.json']:
   assert sha(p)==proof['bindings'][str(p)]==r['bindings'][str(p)];frame=json.loads(p.read_text());assert frame['graph_sha256']==idx['graph_sha256'];records={}
   for q in frame['records']:
    node=q['source'];path=[node]
    for edge in q['answer']['physical_edge_ids']:assert edges[0][edge]==node;dest=edges[1][edge];used.add((node,dest));path.append(dest);node=dest
    assert node==q['sink'];needed.update(path);records[q['connection_id']]={k:q[k] for k in ['connection_id','net_id','source','sink']}|dict(path=tuple(path))
   maps.append(records)
  old,new=maps;assert set(old)==set(new)==set(range(115572));changed=[c for c in old if old[c]['path']!=new[c]['path']];assert len(changed)==14;assert set(map(int,stages[0]['pending_features']))==set(changed);data.append((case,stages,old,new,changed,frozenset(used)))
 graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)==r['bindings'][str(graph)]==idx['graph_sha256'];geo={};stack=[]
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   node=int(n.get('id'))
   if node in needed:
    loc=n.find('loc');assert int(n.get('capacity'))>0;geo[node]=(n.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')))
   parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert set(geo)==needed;rows=[]
 for case,stages,old,new,changed,used in data:
  bynet=collections.defaultdict(list)
  for c in changed:bynet[old[c]['net_id']].append(c)
  group=next(cs for net,cs in sorted(bynet.items()) if len(cs)>1);cache=Cache(idx['graph_sha256'],geo,list(old.values()),lambda a,b:(a,b) in used);base=cache.view()
  try:cache.prepare_paths(idx['graph_sha256'],0,{group[0]:new[group[0]]['path']})
  except ValueError as e:assert 'multiple parents' in str(e)
  else:raise AssertionError('inconsistent real partial replacement accepted')
  assert cache.generation==0 and all(base.query(c)==old[c] for c in changed)
  ticket=cache.prepare_paths(idx['graph_sha256'],0,{c:new[c]['path'] for c in changed});cache.commit(ticket);current=cache.view();assert all(current.query(c)==new[c] for c in new);snap=current.snapshot();counts=collections.defaultdict(collections.Counter);sources={}
  for c,q in new.items():counts[q['net_id']].update(q['path']);sources[q['net_id']]=q['source']
  for net,v in snap['nets'].items():assert v['references']==dict(counts[net]) and v['frontier']=={sources[net]}|{n for n in counts[net] if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY']}
  retained=collections.defaultdict(set)
  for c,q in old.items():
   if c not in changed:retained[q['net_id']].update(q['path'])
  for c in changed:
   q=old[c];nodes={q['source']}|{n for n in retained[q['net_id']] if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY']};b=geo[q['sink']];dist=[]
   for n in nodes:
    a=geo[n]
    if a[5]==b[5]:dist.append(max(0,a[1]-b[2],b[1]-a[2])+max(0,a[3]-b[4],b[3]-a[4]))
   f=stages[0]['pending_features'][str(c)];assert f['published'] is False and f['generation']==1 and f['graph_epoch']==idx['graph_sha256'] and f['frontier_nodes']==len(nodes) and f['same_layer_frontier_nodes']==len(dist) and f['min_tile_L1']==(min(dist) if dist else None)
  rows.append(dict(case=case,direct_replacement_query_states_verified=115572,NETs_verified=len(counts),real_inconsistent_partial_batch_rejected=True,pending_frontiers_verified=14));print('EXTERNAL REAL RESTORE AND PARTIAL REJECTION PASS',case,flush=True)
 for p,h in r['bindings'].items():assert sha(p)==h
 bindings={str(p):sha(p) for p in [rp,Path(__file__),R/'tools/retained_tree_frontier_state_v2.py']}
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all3_admitted_real_roundtrip_fixtures_direct_replacements_and_partial_batch_rejections_verified',bindings=bindings,rows=rows,scope='Admitted model path changes only. Original cold quality gates and remaining overflows unchanged. Node-topology update correctness is not accepted native routing, RC/capacity admission for arbitrary new paths or measured full-flow speed.'),f,indent=2)
if __name__=='__main__':main()
