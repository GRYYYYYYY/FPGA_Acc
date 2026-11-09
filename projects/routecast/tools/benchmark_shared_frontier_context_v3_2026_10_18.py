"""Fixed AB/BA component lifecycle comparison,3source states per shared RR graph."""
import array,collections,copy,gc,json,sys,time,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from retained_tree_frontier_state_v2 import Cache as V2
from retained_tree_frontier_state_v3 import Cache as V3,GraphContext

def main():
 E=R/'experiments';out=E/'mmc_shared_frontier_context_cost_v3_2026-10-18';out.mkdir(exist_ok=False);graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';idxp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';idx=json.loads(idxp.read_text());gp=E/'mmc_endpoint_geometry_topology_v2_2026-10-18/receipt.json';gvp=gp.parent/'independent_verification_v1.json';g=json.loads(gp.read_text());gv=json.loads(gvp.read_text());assert sha(gp)==gv['bindings'][str(gp)] and sha(idxp)==g['bindings'][str(idxp)] and sha(graph)==g['bindings'][str(graph)]==idx['graph_sha256'];fp=E/'mmc_joint_channel_diamond_v1_2026-10-18/independent_full_frame_v1.json';proof=json.loads(fp.read_text());bindings={str(p):sha(p) for p in [graph,idxp,gp,gvp,fp,Path(__file__),R/'tools/retained_tree_frontier_state_v3.py',R/'tools/retained_tree_frontier_state_v2.py',R/'tools/retained_tree_frontier_state_v1.py',R/'tools/incremental_IPIN_feature_cache_v1.py']};plan=dict(order=[['v2_private_geometry','v3_shared_context'],['v3_shared_context','v2_private_geometry']],cases=['case_01','case_02','case_03'],candidates_per_source=1,stages=['remove14','restore14','replace_back14'],cost='Component lifecycle only, given decoded preadmitted paths and full immutable RR geometry/CSR checker. New arm charges1GraphContext plus3path/NET source initializations. Old arm charges3complete source initializations. Both reuse an admitted source state for each child. Charge child/history/source release and final shared-context release. Record forced process-wide GC separately; do not equate it to normal mandatory release cost.',validation='Both arms/stages match independently reconstructed complete CID and NET states; parent and all historical states retained and checked. Neither source path checks nor final-batch NET checks skipped.',limitations='Graph/XML loading, source conversion, CSR construction, file IO, physical/RC/canonical/native routing and debug snapshots are outside paired component boundary. Two paired runs in AB/BA order are descriptive, not full-flow or hardware evidence. Original known failed candidate quality gates remain unchanged.')
 (out/'protocol.json').write_text(json.dumps(plan,indent=2));tick=time.perf_counter();geo={};stack=[]
 for event,n in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(n);continue
  parent=stack[-2] if len(stack)>1 else None
  if n.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   i=int(n.get('id'));loc=n.find('loc');assert i not in geo and int(n.get('capacity'))>0;geo[i]=(n.get('type'),*[int(loc.get(k)) for k in ['xlow','xhigh','ylow','yhigh']],int(loc.get('layer','0')));parent.remove(n);n.clear()
  if n.tag=='rr_nodes':break
  stack.pop()
 assert len(geo)==904438;geometry_load=time.perf_counter()-tick;edges=[]
 for name in ['edge_source','edge_destination']:
  d=idx['arrays'][name];assert sha(d['path'])==d['sha256']==g['bindings'][d['path']];bindings[d['path']]=d['sha256'];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());edges.append(a)
 tick=time.perf_counter();offset=array.array('I',[0])*904439
 for source in edges[0]:offset[source+1]+=1
 for n in range(1,len(offset)):offset[n]+=offset[n-1]
 dest=array.array('I',[0])*len(edges[1]);position=array.array('I',offset)
 for a,b in zip(*edges):dest[position[a]]=b;position[a]+=1
 del position;csr_seconds=time.perf_counter()-tick
 def exists(a,b):
  for j in range(offset[a],offset[a+1]):
   if dest[j]==b:return True
  return False
 data={}
 def oracle(records):
  refs=collections.defaultdict(collections.Counter);cids=collections.defaultdict(set);sources={}
  for c,q in records.items():
   net=q['net_id'];sources.setdefault(net,q['source']);assert sources[net]==q['source'];cids[net].add(c)
   if q['path'] is not None:refs[net].update(q['path'])
  nets={net:dict(source=src,cids=frozenset(cids[net]),references=dict(refs[net]),frontier=frozenset([src])|frozenset(n for n in refs[net] if geo[n][0] in ['SOURCE','OPIN','CHANX','CHANY'])) for net,src in sources.items()};return dict(queries=records,nets=nets)
 for case in plan['cases']:
  maps=[]
  for p in [E/f'mmc_multiplacement_models_v1_2026-10-18/{case}/feedback_on/native_retained/sketch.json',E/f'mmc_joint_channel_diamond_v1_2026-10-18/{case}/candidate.json']:
   assert sha(p)==proof['bindings'][str(p)];bindings[str(p)]=sha(p);frame=json.loads(p.read_text());assert frame['graph_sha256']==idx['graph_sha256'];records={}
   for q in frame['records']:
    n=q['source'];path=[n]
    for edge in q['answer']['physical_edge_ids']:assert edges[0][edge]==n;n=edges[1][edge];path.append(n)
    assert n==q['sink'];records[q['connection_id']]={k:q[k] for k in ['connection_id','net_id','source','sink']}|dict(path=tuple(path))
   maps.append(records)
  old,new=maps;assert set(old)==set(new)==set(range(115572));changed=sorted(c for c in old if old[c]!=new[c]);assert len(changed)==14;pending=dict(old)
  for c in changed:pending[c]={**old[c],'path':None}
  data[case]=dict(old=old,new=new,changed=changed,expected=[oracle(old),oracle(pending),oracle(new),oracle(old)])
  print('SHARED CONTEXT INPUT READY',case,flush=True)
 def check(view,wanted):
  s=view.snapshot();assert s['queries']==wanted['queries'] and s['nets']==wanted['nets']
 samples=[]
 for pair,order in enumerate(plan['order']):
  for arm in order:
   gc.collect();context=None;context_init=0.0
   if arm=='v3_shared_context':tick=time.perf_counter();context=GraphContext(idx['graph_sha256'],geo,exists);context_init=time.perf_counter()-tick
   cases=[]
   for case in plan['cases']:
    d=data[case];tick=time.perf_counter();base=V3(context,list(d['old'].values())) if context is not None else V2(idx['graph_sha256'],geo,list(d['old'].values()),exists);initialize=time.perf_counter()-tick;check(base.view(),d['expected'][0]);tick=time.perf_counter()
    if context is not None:child=base.branch(idx['graph_sha256'],0);assert child._state is base._state and child._context is context
    else:child=copy.copy(base);child._pending={};assert child._state is base._state
    branch_seconds=time.perf_counter()-tick;history=[child.view()];stages=[]
    for stage in range(3):
     tick=time.perf_counter()
     if stage==0:ticket=child.prepare(idx['graph_sha256'],child.generation,d['changed'])
     else:ticket=child.prepare_paths(idx['graph_sha256'],child.generation,{c:(d['new'] if stage==1 else d['old'])[c]['path'] for c in d['changed']})
     preview=child.preview(ticket);features={c:preview.feature(c) for c in d['changed']} if stage==0 else {};receipt=child.commit(ticket);history.append(child.view());elapsed=time.perf_counter()-tick;check(history[-1],d['expected'][stage+1]);stages.append(dict(stage=stage,seconds=elapsed,receipt=receipt,features=features))
    check(base.view(),d['expected'][0])
    for i,view in enumerate(history):check(view,d['expected'][i])
    del view;tick=time.perf_counter();del preview,history,child,base,ticket;release=time.perf_counter()-tick;tick=time.perf_counter();collected=gc.collect();explicit_gc=time.perf_counter()-tick
    cases.append(dict(case=case,source_initialize_seconds=initialize,branch_seconds=branch_seconds,stages=stages,reference_release_seconds=release,explicit_gc_seconds=explicit_gc,explicit_gc_objects=collected,full_query_state_comparisons=9*115572));print('SHARED CONTEXT LIFECYCLE PASS',pair,arm,case,initialize,release,explicit_gc,flush=True)
   tick=time.perf_counter();del context;context_release=time.perf_counter()-tick;tick=time.perf_counter();final_gc_objects=gc.collect();final_gc=time.perf_counter()-tick;production=context_init+context_release+sum(x['source_initialize_seconds']+x['branch_seconds']+x['reference_release_seconds']+sum(s['seconds'] for s in x['stages']) for x in cases);gc_total=final_gc+sum(x['explicit_gc_seconds'] for x in cases);samples.append(dict(pair=pair,arm=arm,graph_geometry_admissions=1 if arm=='v3_shared_context' else 3,source_path_NET_admissions=3,shared_graph_context_initialize_seconds=context_init,shared_graph_context_release_seconds=context_release,cases=cases,component_lifecycle_seconds_without_explicit_gc=production,explicit_gc_seconds=gc_total,component_lifecycle_plus_explicit_gc_seconds=production+gc_total,final_gc_objects=final_gc_objects))
 assert len(samples)==4 and all(sha(p)==h for p,h in bindings.items())
 with (out/'results.json').open('x') as f:json.dump(dict(status='all4_balanced_component_lifecycles_and_complete_state_oracles_pass',bindings=bindings,samples=samples,common_geometry_XML_load_seconds=geometry_load,common_full_CSR_build_seconds=csr_seconds,scope=plan['limitations']),f,indent=2)
if __name__=='__main__':main()
