"""Three admitted model-path roundtrips and complete cache lifecycle boundaries."""
import array,collections,copy,gc,json,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from retained_tree_frontier_state_v2 import Cache

def main():
 E=R/'experiments';out=E/'mmc_source_frontier_restore_real_v2_2026-10-18';out.mkdir(exist_ok=False);graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());proofp=E/'mmc_joint_channel_diamond_v1_2026-10-18/independent_full_frame_v1.json';proof=json.loads(proofp.read_text());geop=E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json';gvp=geop.parent/'independent_verification_v1.json';gp=json.loads(geop.read_text());gv=json.loads(gvp.read_text());assert sha(geop)==gv['bindings'][str(geop)] and sha(graph)==gp['bindings'][str(graph)]==idx['graph_sha256'] and sha(idxp)==gp['bindings'][str(idxp)];corep=E/'retained_tree_frontier_restore_core_v2_2026-10-18/verification.json';core=json.loads(corep.read_text());assert core['commits']==320;bindings={str(p):sha(p) for p in [graph,idxp,proofp,geop,gvp,corep,Path(__file__),R/'tools/retained_tree_frontier_state_v2.py',R/'tools/retained_tree_frontier_state_v1.py',R/'tools/incremental_IPIN_feature_cache_v1.py']};geo={};stack=[];tick=time.perf_counter()
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   node=int(n.get('id'));assert int(n.get('capacity'))>0 and node not in geo;loc=n.find('loc');geo[node]=(n.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')));parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert len(geo)==904438;geometry_seconds=time.perf_counter()-tick;edges=[]
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==gp['bindings'][d['path']];bindings[d['path']]=d['sha256'];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());edges.append(a)
 plan=dict(selection='All3previously admitted joint-diamond candidates,14changed queries in8NETs percase. Their original cold quality gates failed; these are state-maintenance fixtures only, not a new routing policy trial.',stages=['remove14paths and query pending frontiers','restore14candidate paths','replace14paths back to original'],checks='Full115572CID and55300NET state rebuild perstage, immutable historical views, final-batch topology, candidate/source file bindings and staged feature parity.',cost='One descriptive lifecycle percase, not a balanced performance benchmark. Report state initialization,3prepare/commit phases,14pending feature queries and release of staged/historical child views. Common graph geometry, file decode, edge-to-path conversion and original physical/RC admission are separate. Debug snapshot validation is outside measured production phases. Full rebuild oracle cost is diagnostic; representation and admission boundaries differ, no end-to-end speed claim.')
 (out/'protocol.json').write_text(json.dumps(plan,indent=2));rows=[]
 for case in ['case_01','case_02','case_03']:
  oldp=E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/sketch.json';newp=E/f'mmc_joint_channel_diamond_v1_2026-10-18/{case}/candidate.json';assert sha(oldp)==proof['bindings'][str(oldp)] and sha(newp)==proof['bindings'][str(newp)];bindings[str(oldp)]=sha(oldp);bindings[str(newp)]=sha(newp);frames=[json.loads(p.read_text()) for p in [oldp,newp]];maps=[];used=set()
  for frame in frames:
   assert frame['graph_sha256']==idx['graph_sha256'];records={}
   for r in frame['records']:
    current=r['source'];path=[current]
    for edge in r['answer']['physical_edge_ids']:assert edges[0][edge]==current;dest=edges[1][edge];used.add((current,dest));path.append(dest);current=dest
    assert current==r['sink'];records[r['connection_id']]={k:r[k] for k in ['connection_id','net_id','source','sink']}|dict(path=tuple(path))
   maps.append(records)
  original,candidate=maps;assert set(original)==set(candidate)==set(range(115572));assert all({k:v for k,v in original[c].items() if k!='path'}=={k:v for k,v in candidate[c].items() if k!='path'} for c in original);changed=sorted(c for c in original if original[c]['path']!=candidate[c]['path']);assert len(changed)==14 and len({original[c]['net_id'] for c in changed})==8;tick=time.perf_counter();cache=Cache(idx['graph_sha256'],geo,list(original.values()),lambda a,b:(a,b) in used);init_seconds=time.perf_counter()-tick;retained=[cache.view()];expected=dict(original);stages=[];queries=0
  for stage in range(3):
   tick=time.perf_counter()
   if stage==0:ticket=cache.prepare(idx['graph_sha256'],cache.generation,changed)
   else:ticket=cache.prepare_paths(idx['graph_sha256'],cache.generation,{c:(candidate if stage==1 else original)[c]['path'] for c in changed})
   preview=cache.preview(ticket);features={c:preview.feature(c) for c in changed} if stage==0 else {};receipt=cache.commit(ticket);incremental=time.perf_counter()-tick;current=cache.view();retained.append(current)
   if stage==0:
    for c in changed:expected[c]={**expected[c],'path':None}
   else:
    for c in changed:expected[c]=(candidate if stage==1 else original)[c]
   tick=time.perf_counter();refs=collections.defaultdict(collections.Counter);sources={};cids=collections.defaultdict(set);parent=collections.defaultdict(dict)
   for cid,r in expected.items():
    net=r['net_id'];sources.setdefault(net,r['source']);assert sources[net]==r['source'];cids[net].add(cid)
    if r['path'] is None:continue
    refs[net].update(r['path'])
    for a,b in zip(r['path'],r['path'][1:]):assert b not in parent[net] or parent[net][b]==a;parent[net][b]=a
   frontiers={net:frozenset([src])|frozenset(n for n in refs[net] if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY']) for net,src in sources.items()};rebuild=time.perf_counter()-tick;snapshot=current.snapshot();assert snapshot['queries']==expected
   for net,v in snapshot['nets'].items():assert v['source']==sources[net] and v['cids']==cids[net] and v['references']==dict(refs[net]) and v['frontier']==frontiers[net]
   for c,f in features.items():
    q=expected[c];b=geo[q['sink']];ds=[]
    for n in frontiers[q['net_id']]:
     a=geo[n]
     if a[5]==b[5]:ds.append(max(0,max(a[1],b[1])-min(a[2],b[2]))+max(0,max(a[3],b[3])-min(a[4],b[4])))
    assert f['min_tile_L1']==(min(ds) if ds else None) and f['frontier_nodes']==len(frontiers[q['net_id']]);queries+=1
   assert all(retained[0].query(c)==original[c] for c in changed)
   if stage>=1:assert all(retained[1].query(c)['path'] is None for c in changed)
   if stage==2:assert all(retained[2].query(c)==candidate[c] for c in changed)
   stages.append(dict(stage=stage,generation=current.generation,incremental_prepare_query_commit_seconds=incremental,independent_full_state_tree_rebuild_seconds=rebuild,query_states_verified=115572,NET_states_verified=len(sources),receipt=receipt,pending_features=features));print('REAL FRONTIER RESTORE STAGE PASS',case,stage,current.generation,incremental,rebuild,flush=True)
  assert all(cache.view().query(c)==original[c] for c in original);tick=time.perf_counter();del retained,preview,current,ticket;gc.collect();release=time.perf_counter()-tick;folder=out/case;folder.mkdir();artifact=folder/'stages.json'
  with artifact.open('x') as f:json.dump(stages,f,indent=2)
  rows.append(dict(case=case,changed_CIDs=14,changed_NETs=8,stages_verified=3,query_states_verified=3*115572,pending_features_verified=queries,state_initialization_seconds=init_seconds,incremental_stage_seconds=sum(s['incremental_prepare_query_commit_seconds'] for s in stages),historical_child_view_release_gc_seconds=release,initialization_update_query_release_seconds=init_seconds+sum(s['incremental_prepare_query_commit_seconds'] for s in stages)+release,diagnostic_full_rebuild_seconds=sum(s['independent_full_state_tree_rebuild_seconds'] for s in stages),artifact=str(artifact),artifact_sha256=sha(artifact)))
  del cache,frames,original,candidate,maps,expected,snapshot,refs,frontiers,parent,used
 assert len(rows)==3 and all(sha(p)==h for p,h in bindings.items())
 with (out/'verification.json').open('x') as f:json.dump(dict(status='all3_real_remove_restore_replace_roundtrips_full_state_and_history_checks_pass',bindings=bindings,rows=rows,graph_geometry_load_seconds=geometry_seconds,cost_scope=plan['cost'],scope='Model state maintenance only; candidate paths retain known overflows and failed original cold gates. No repaired route acceptance, native prediction parity or accepted complete-time benefit.'),f,indent=2)
if __name__=='__main__':main()
