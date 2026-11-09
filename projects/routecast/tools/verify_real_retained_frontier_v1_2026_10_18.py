"""External input-admission chain and sparse affected-NET path-union verification."""
import array,collections,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';root=E/'mmc_source_retained_frontier_real_v1_2026-10-18';rp=root/'verification.json';r=json.loads(rp.read_text());assert len(r['rows'])==9;cp=E/'mmc_native_connection_CID_binding_v1_2026-10-18/independent_verification_v1.json';cidproof=json.loads(cp.read_text());gp=E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json';gvp=gp.parent/'independent_verification_v1.json';geoproof=json.loads(gp.read_text());gverify=json.loads(gvp.read_text());assert sha(gp)==gverify['bindings'][str(gp)];idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());assert sha(idxp)==geoproof['bindings'][str(idxp)];graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';assert sha(graph)==idx['graph_sha256']==geoproof['bindings'][str(graph)];edges=[];bindings={str(p):sha(p) for p in [rp,cp,gp,gvp,Path(__file__)]}
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==geoproof['bindings'][d['path']];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());edges.append(a)
 targetproofp=E/'prospective_layout_swap_native_deltas_v1_2026-10-18/verification.json';targetproof=json.loads(targetproofp.read_text());fullproofp=E/'mmc_joint_channel_diamond_v1_2026-10-18/independent_full_frame_v1.json';fullproof=json.loads(fullproofp.read_text());data=[];needed=set();frames={}
 for row in r['rows']:
  case,episode=row['case'],row['episode'];fp=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/sketch.json'
  if case not in frames:
   assert sha(fp)==fullproof['bindings'][str(fp)];frame=json.loads(fp.read_text());frames[case]={q['connection_id']:q for q in frame['records']};assert frame['graph_sha256']==idx['graph_sha256'] and set(frames[case])==set(range(115572))
  old=frames[case];partp=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/scope_partition.json';assert sha(partp)==cidproof['bindings'][str(partp)]==r['bindings'][str(partp)];original=json.loads(partp.read_text())['physical_to_original_connection_ids'];translation={x['physical_connection_id']:x['original_connection_id'] for x in original};folder=E/f'prospective_layout_swap_native_partition_v1_2026-10-18/episode_{episode:02d}';ep=folder/'endpoints.json';pp=folder/'partition.json';assert sha(ep)==targetproof['bindings'][str(ep)] and sha(pp)==targetproof['bindings'][str(pp)];new={q['connection_id']:q for q in json.loads(ep.read_text())['connections']};assert set(new)==set(old) and list(translation.values())==json.loads(pp.read_text())['physical_to_original_connection_ids'];assert all(new[c]['net_id']==old[c]['net_id'] for c in old);removed={c for c in old if (old[c]['source'],old[c]['sink'])!=(new[c]['source'],new[c]['sink'])};nets={old[c]['net_id'] for c in removed};artifactp=Path(row['artifact']);assert sha(artifactp)==row['artifact_sha256'];artifact=json.loads(artifactp.read_text());assert set(artifact['removed_CIDs'])==removed and set(map(int,artifact['features']))==removed;retained=collections.defaultdict(set);cids_by_net=collections.defaultdict(list)
  for c,q in old.items():
   if q['net_id'] not in nets:continue
   cids_by_net[q['net_id']].append(c)
   if c in removed:continue
   node=q['source'];retained[q['net_id']].add(node)
   for edge in q['answer']['physical_edge_ids']:assert edges[0][edge]==node;node=edges[1][edge];retained[q['net_id']].add(node)
   assert node==q['sink']
  sources={net:next(iter({new[c]['source'] for c in cs})) for net,cs in cids_by_net.items()};assert all(len({new[c]['source'] for c in cs})==1 for cs in cids_by_net.values());expected_source_edits={net:src for net,src in sources.items() if src!=old[cids_by_net[net][0]]['source']};assert {int(n):src for n,src in artifact['source_updates'].items()}==expected_source_edits
  for net,src in expected_source_edits.items():assert set(cids_by_net[net])<=removed and not retained[net]
  for net in nets:needed.update(retained[net]);needed.add(sources[net])
  needed.update(new[c]['sink'] for c in removed);data.append((row,artifact,new,removed,retained,sources));bindings[str(artifactp)]=sha(artifactp)
 geo={};stack=[]
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
 assert set(geo)==needed;checked=0;rows=[]
 for row,artifact,new,removed,retained,sources in data:
  frontiers={net:{src}|{n for n in retained[net] if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY']} for net,src in sources.items()}
  for c in removed:
   q=new[c];f=artifact['features'][str(c)];nodes=frontiers[q['net_id']];assert geo[q['source']][0]=='SOURCE' and geo[q['sink']][0]=='SINK';b=geo[q['sink']];dist=[]
   for n in nodes:
    a=geo[n]
    if a[5]!=b[5]:continue
    dx=max(a[1],b[1])-min(a[2],b[2]);dy=max(a[3],b[3])-min(a[4],b[4]);dist.append(max(0,dx)+max(0,dy))
   assert f['graph_epoch']==idx['graph_sha256'] and f['generation']==1 and f['published'] is False and f['retained_path'] is False and f['connection_id']==c and f['net_id']==q['net_id'];assert (f['frontier_nodes'],f['same_layer_frontier_nodes'],f['min_tile_L1'])==(len(nodes),len(dist),min(dist) if dist else None);checked+=1
  rows.append(dict(case=row['case'],episode=row['episode'],features_verified=len(removed),source_NET_invalidations=len(artifact['source_updates'])));print('EXTERNAL SOURCE FRONTIER PASS',row['case'],row['episode'],len(removed),flush=True)
 assert checked==sum(x['features_verified'] for x in r['rows'])
 for p,h in r['bindings'].items():assert sha(p)==h
 bindings.update({str(targetproofp):sha(targetproofp),str(fullproofp):sha(fullproofp)})
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all9_admitted_CID_translations_and_source_only_retained_frontier_features_independently_verified',bindings=bindings,features_verified=checked,rows=rows,scope='External recomputation of every emitted feature from affected-NET surviving sibling paths and original XML, plus certified original-CID translation chains. Primary real harness separately compares entire115572CID/55300NET state to full reconstruction. No native-frontier parity, pending-path repair or complete-time benefit certified.'),f,indent=2)
if __name__=='__main__':main()
