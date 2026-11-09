"""Nine admitted-layout transitions; independent complete source path-union oracle."""
import array,collections,copy,json,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from retained_tree_frontier_state_v1 import Cache

def main():
 E=R/'experiments';out=E/'mmc_source_retained_frontier_real_v1_2026-10-18';out.mkdir(exist_ok=False);graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';ip=E/'real_joint_full_score_v2_2026-10-18/verification.json';idx=json.loads(idxp.read_text());indexproof=json.loads(ip.read_text());assert sha(idxp)==indexproof['bindings'][str(idxp)];graph_sha=sha(graph);assert graph_sha==idx['graph_sha256'];proofp=E/'mmc_joint_channel_diamond_v1_2026-10-18/independent_full_frame_v1.json';proof=json.loads(proofp.read_text());targetproofp=E/'prospective_layout_swap_native_deltas_v1_2026-10-18/verification.json';targetproof=json.loads(targetproofp.read_text());corep=E/'retained_tree_frontier_core_v1_2026-10-18/verification.json';core=json.loads(corep.read_text());assert core['commits']==120;bindings={str(p):sha(p) for p in [graph,idxp,ip,proofp,targetproofp,corep,Path(__file__),R/'tools/retained_tree_frontier_state_v1.py',R/'tools/incremental_IPIN_feature_cache_v1.py']};rows=[];stack=[];geo={};tick=time.perf_counter()
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   i=int(n.get('id'));loc=n.find('loc');assert i not in geo and int(n.get('capacity'))>0;geo[i]=(n.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')));parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert len(geo)==904438;graph_geometry_seconds=time.perf_counter()-tick;edges=[]
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256'];bindings[d['path']]=d['sha256'];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());assert len(a)==8097539 and sys.byteorder=='little';edges.append(a)
 targets={};translations={}
 for episode in range(1,4):
  folder=E/f'prospective_layout_swap_native_partition_v1_2026-10-18/episode_{episode:02d}';p=folder/'endpoints.json';pp=folder/'partition.json';assert sha(p)==targetproof['bindings'][str(p)] and sha(pp)==targetproof['bindings'][str(pp)];ep=json.loads(p.read_text());assert ep['graph_sha256']==graph_sha;targets[episode]={q['connection_id']:q for q in ep['connections']};translations[episode]=json.loads(pp.read_text())['physical_to_original_connection_ids'];bindings[str(p)]=sha(p);bindings[str(pp)]=sha(pp)
 protocol=dict(selection='All3previously admitted current model native_retained_on frames x all3independently admitted development swap placements;9transitions, no outcome selection. Complete original CID translations and logicalNET identities must agree.',frontier='Union of still-retained query paths excluding IPIN/SINK, plus current SOURCE. SOURCE relocation invalidates all NET paths automatically. No native seed labels or routing outcomes read.',timing='One descriptive component measurement per transition, not a repeated performance claim. Preloaded graph/paths/endpoints; separate full endpoint-difference scan, sparse state prepare/query/commit, independent whole-state rebuild oracle and initial state construction. Graph/XML/file IO and complete physical admission listed separately or excluded equally. No end-to-end gain claim.',scope='Source-only geometry/state correctness and cost boundary. Pending connections have no repaired paths; no native frontier parity or original cold/native gate promotion.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2))
 for case in ['case_01','case_02','case_03']:
  fp=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/sketch.json';assert sha(fp)==proof['bindings'][str(fp)];bindings[str(fp)]=sha(fp);frame=json.loads(fp.read_text());assert frame['graph_sha256']==graph_sha;partp=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/scope_partition.json';part=json.loads(partp.read_text())['physical_to_original_connection_ids'];translation=[v['original_connection_id'] for v in sorted(part,key=lambda x:x['physical_connection_id'])];assert all(translation==t for t in translations.values());bindings[str(partp)]=sha(partp);records=[];used=set();by_net=collections.defaultdict(list)
  for r in frame['records']:
   node=r['source'];path=[node]
   for edge in r['answer']['physical_edge_ids']:
    assert edges[0][edge]==node;target=edges[1][edge];used.add((node,target));path.append(target);node=target
   assert node==r['sink'];records.append({k:r[k] for k in ['connection_id','net_id','source','sink']}|dict(path=path));by_net[r['net_id']].append(r['connection_id'])
  old={r['connection_id']:r for r in records};assert set(old)==set(range(115572));tick=time.perf_counter();cache=Cache(graph_sha,geo,records,lambda a,b:(a,b) in used);initialization=time.perf_counter()-tick;view=cache.view();baseline_generation=view.generation
  for episode,new in targets.items():
   assert set(new)==set(old) and all(new[c]['net_id']==old[c]['net_id'] for c in old);tick=time.perf_counter();removed=[c for c in old if (old[c]['source'],old[c]['sink'])!=(new[c]['source'],new[c]['sink'])];sinks={c:new[c]['sink'] for c in removed if new[c]['sink']!=old[c]['sink']};sources={old[c]['net_id']:new[c]['source'] for c in removed if new[c]['source']!=old[c]['source']};assert all(len({new[c]['source'] for c in cids})==1 for cids in by_net.values());discovery=time.perf_counter()-tick
   child=copy.copy(cache);child._pending={};tick=time.perf_counter();token=child.prepare(graph_sha,0,removed,sinks,sources);preview=child.preview(token);features={c:preview.feature(c) for c in removed};receipt=child.commit(token);incremental=time.perf_counter()-tick;current=child.view();assert current.generation==1 and view.generation==baseline_generation==0
   tick=time.perf_counter();removed_set=set(removed);counts=collections.defaultdict(collections.Counter);expected_queries={};net_sources={}
   for c,r in old.items():
    q=new[c];net=r['net_id'];net_sources.setdefault(net,q['source']);assert net_sources[net]==q['source'];path=None if c in removed_set else tuple(r['path']);expected_queries[c]=dict(connection_id=c,net_id=net,source=q['source'],sink=q['sink'],path=path)
    if path is not None:counts[net].update(path)
   frontiers={net:frozenset([src])|frozenset(n for n in counts[net] if geo[n][0] not in ['IPIN','SINK']) for net,src in net_sources.items()};expected_features={}
   for c in removed:
    q=new[c];nodes=frontiers[q['net_id']];b=geo[q['sink']];dist=[]
    for n in nodes:
     a=geo[n]
     if a[5]!=b[5]:continue
     dx=b[1]-a[2] if a[2]<b[1] else a[1]-b[2] if b[2]<a[1] else 0;dy=b[3]-a[4] if a[4]<b[3] else a[3]-b[4] if b[4]<a[3] else 0;dist.append(dx+dy)
    expected_features[c]=(len(nodes),len(dist),min(dist) if dist else None)
   rebuild=time.perf_counter()-tick;snapshot=current.snapshot();assert set(snapshot['queries'])==set(old) and snapshot['queries']==expected_queries
   for net,n in snapshot['nets'].items():assert n['source']==net_sources[net] and n['references']==dict(counts[net]) and n['frontier']==frontiers[net]
   for c,f in features.items():assert not f['published'] and not f['retained_path'] and (f['frontier_nodes'],f['same_layer_frontier_nodes'],f['min_tile_L1'])==expected_features[c]
   assert view.query(0)['path']==tuple(old[0]['path']) and view.generation==0;folder=out/(case+f'__episode_{episode:02d}');folder.mkdir();artifact=dict(removed_CIDs=removed,sink_updates=sinks,source_updates=sources,features=features,receipt=receipt)
   with (folder/'features.json').open('x') as f:json.dump(artifact,f,indent=2)
   rows.append(dict(case=case,episode=episode,CIDs_verified=115572,NETs_verified=len(net_sources),removed_CIDs=len(removed),source_NET_invalidations=len(sources),features_verified=len(features),state_initialization_seconds=initialization,endpoint_difference_seconds=discovery,sparse_prepare_query_commit_seconds=incremental,independent_full_rebuild_seconds=rebuild,artifact=str(folder/'features.json'),artifact_sha256=sha(folder/'features.json')));print('REAL SOURCE FRONTIER PASS',case,episode,len(removed),len(sources),discovery,incremental,rebuild,flush=True)
  del frame,records,cache,old,view,child,current,snapshot
 assert len(rows)==9
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all9_real_layout_transition_complete_CID_NET_frontier_checks_pass',bindings=bindings,rows=rows,RR_nodes=904438,graph_geometry_load_seconds=graph_geometry_seconds,scope=protocol['scope'],timing_scope=protocol['timing']),f,indent=2)
if __name__=='__main__':main()
