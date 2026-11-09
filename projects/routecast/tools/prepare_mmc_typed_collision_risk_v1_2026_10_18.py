"""Source-only type-consistent mean/overflow risk priors with NET ownership."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache
from net_group_collision_risk_v1 import unit_group_expectation

def main():
 forecast=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18';fp=R/'experiments/mmc_geometry_pool_verification_v1_2026-10-18/verification.json';f=json.loads(fp.read_text());assert f['status']=='pass'
 core=R/'experiments/net_group_collision_risk_core_v1_2026-10-18/verification.json';c=json.loads(core.read_text());assert c['status']=='pass'
 config=json.loads((forecast/'protocol.json').read_text());bindings={**f['bindings'],**c['bindings'],str(fp):sha(fp),str(core):sha(core),**closure([Path(__file__)])}
 d=R/'experiments/mmc_typed_collision_risk_v1_2026-10-18';d.mkdir();(d/'vectors').mkdir();cases=['case_01','case_02','case_03'];methods=config['source_methods']
 protocol=d/'protocol.json'
 with protocol.open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=config['inputs'],methods=methods,score_families=['observed_overflow','typed_group_mean','typed_NET_collision'],primary_new_family='typed_NET_collision',channel_groups='Exactly existing graph-only geometry/direction/segment/RC groups; require all members capacity1.',IPIN_groups='All positive-capacity IPINs with outgoing arcs exclusively to one positive terminal SINK (SINK outdegree0); group by that SINK. Group requires all members capacity1. No target-pressure or initial-overuse filter.',prior='Each NET independently chooses k distinct resources uniformly within its group, where k is its current unique group ownership. Per-member Eoverflow=sum(k/m)-1+product(1-k/m). Group membership is NOT a guarantee of per-query reachability, RC feasibility or native sampling.',fallback='Every positive RR outside eligible groups uses deterministic max(0,current_uniqueNET_occupancy-capacity)/capacity in all new type-consistent families. SOURCE/SINK/OPIN fixed-resource treatment is explicit; unsupported IPINs are reported and retained.',controls='Existing12 frozen density baselines remain. New observed_overflow per-source baseline and typed_group_mean isolate deterministic overuse and same-group mean versus nonlinear shared-NET collision expectation. All6 sources,3cases and all positiveRR domains required; no fitted weights or primary/source/label reselection.',scope='Materialize source-only risk scores before new score outcomes. Not paths/native seed or calibrated native pressure. Legacy cold/native utility failures and strict unseen0 remain.'),stream,indent=2)
 bindings[str(protocol)]=sha(protocol);cache=Cache();summaries=[];manifest={}
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  ep=json.loads(Path(config['inputs']['case_01']['endpoint']).read_text());graph=Path(ep['inputs']['graph']['path']);caps=array('I');kinds=[];dest=array('I');outdegree=None;terminal=None;stack=[]
  for event,e in ET.iterparse(graph,events=('start','end')):
   if event=='start':
    stack.append(e)
    if e.tag=='rr_edges':outdegree=array('I',[0])*len(caps);terminal=array('i',[-2])*len(caps)
    continue
   parent=stack[-2].tag if len(stack)>1 else None
   if e.tag=='node' and parent=='rr_nodes':
    assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));stack[-2].remove(e);e.clear()
   elif e.tag=='edge' and parent=='rr_edges':
    u,v=int(e.get('src_node')),int(e.get('sink_node'));assert u<len(caps) and v<len(caps);dest.append(v);outdegree[u]+=1
    if kinds[u]=='IPIN':terminal[u]=v if terminal[u]==-2 else terminal[u] if terminal[u]==v else -1
    stack[-2].remove(e);e.clear()
   stack.pop()
  assert len(caps)==904438 and len(dest)==8097539
  groups=[];assigned={};fallback_reasons={};inventory=json.loads((forecast/'groups.json').read_text());assert inventory['graph_sha256']==sha(graph)
  for old in inventory['groups']:
   nodes=[n for n,cap in old['members']];assert all(caps[n]==1 and kinds[n] in ['CHANX','CHANY'] for n in nodes)
   gid=len(groups);groups.append(dict(kind='geometry_channel',members=nodes,geometry_key=old['key']))
   for n in nodes:assert n not in assigned;assigned[n]=gid
  pools=defaultdict(list)
  for n,kind in enumerate(kinds):
   if kind!='IPIN' or caps[n]==0:continue
   sink=terminal[n]
   if sink>=0 and kinds[sink]=='SINK' and caps[sink]>0 and outdegree[sink]==0:pools[sink].append(n)
   else:fallback_reasons[n]='IPIN_not_single_terminal_SINK_pool'
  for sink,nodes in sorted(pools.items()):
   if any(caps[n]!=1 for n in nodes):
    for n in nodes:fallback_reasons[n]='IPIN_pool_nonunit_capacity'
    continue
   gid=len(groups);groups.append(dict(kind='direct_sink_IPIN',sink_RR=sink,members=nodes))
   for n in nodes:assert n not in assigned;assigned[n]=gid
  positive=[n for n,cap in enumerate(caps) if cap>0]
  for n in positive:
   if n not in assigned and n not in fallback_reasons:fallback_reasons[n]='fixed_or_unsupported_type_'+kinds[n]
  assert set(positive)==set(assigned)|set(fallback_reasons) and set(assigned).isdisjoint(fallback_reasons)
  group_path=d/'groups.json'
  with group_path.open('x') as stream:json.dump(dict(graph_sha256=sha(graph),groups=groups,positive_RR_ids=positive,fallback_reasons=fallback_reasons,coverage_by_type={kind:dict(total=sum(k==kind and caps[n]>0 for n,k in enumerate(kinds)),grouped=sum(kinds[n]==kind for n in assigned),fallback=sum(kinds[n]==kind for n in fallback_reasons)) for kind in sorted(set(kinds))},byteorder=sys.byteorder,array_type='double',array_itemsize=8),stream)
  bindings[str(group_path)]=sha(group_path)
  print('TYPED GROUPS FROZEN',len(groups),'positiveRR',len(positive),'IPINpools',sum(g['kind']=='direct_sink_IPIN' for g in groups),flush=True)
  for case in cases:
   for method in methods:
    framepath=Path(config['inputs'][case]['predictions'][method]);assert bindings[str(framepath)]==sha(framepath);frame=json.loads(framepath.read_text())
    if method=='previous_native':
     proof=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/independent_xml_verification_v1.json';v=json.loads(proof.read_text());assert v['all_native_paths_exact'] and v['bindings'][str(framepath)]==sha(framepath) and v['bindings'][str(graph)]==sha(graph)
    else:assert frame['graph_sha256']==sha(graph)
    ledger={int(n):v for n,v in frame['ledger'].items() if v};nets=defaultdict(list)
    for record in frame['records']:nets[record['net_id']].append(record)
    hist=[Counter() for _ in groups];rebuilt=Counter()
    for net,records in nets.items():
     owned={r['source'] for r in records}|{dest[e] for r in records for e in r['answer']['physical_edge_ids']};rebuilt.update(owned)
     counts=Counter(assigned[n] for n in owned if n in assigned)
     for gid,k in counts.items():hist[gid][k]+=1
    assert dict(rebuilt)==ledger
    expectation={};journal={}
    for gid,g in enumerate(groups):
     if not hist[gid]:continue
     size=len(g['members']);result=unit_group_expectation(size,hist[gid]);mass=sum(ledger.get(n,0) for n in g['members'])
     assert result['expected_occupancy']*size==mass==sum(k*count for k,count in hist[gid].items())
     expectation[gid]=result;journal[gid]=dict(NET_occupancy_histogram=dict(hist[gid]),expected_occupancy=str(result['expected_occupancy']),probability_empty=str(result['probability_empty']),expected_overflow=str(result['expected_overflow']))
    references={}
    for family in ['observed_overflow','typed_group_mean','typed_NET_collision']:
     values=array('d')
     for n in positive:
      value=Fraction(max(0,ledger.get(n,0)-caps[n]),caps[n])
      if family!='observed_overflow' and n in assigned:
       result=expectation.get(assigned[n]);value=Fraction(0) if result is None else result['expected_occupancy' if family=='typed_group_mean' else 'expected_overflow']
      values.append(float(value))
     path=d/'vectors'/(case+'__'+method+'__'+family+'.f64')
     with path.open('xb') as stream:values.tofile(stream)
     references[family]=dict(path=str(path),sha256=sha(path),values=len(values));manifest[case+'__'+method+'__'+family]=references[family]
    target=d/(case+'__'+method+'.json')
    with target.open('x') as stream:json.dump(dict(schema='ROUTECAST_TYPED_NET_COLLISION_RISK_V1',case=case,source_method=method,source_frame_sha256=sha(framepath),groups_sha256=sha(group_path),positive_group_histograms=journal,implicit_empty_group=dict(expected_occupancy='0',probability_empty='1',expected_overflow='0'),vectors=references,uniqueNET_ledger_rebuilt_exactly=True),stream)
    bindings[str(target)]=sha(target);summaries.append(dict(case=case,method=method,NETs=len(nets),active_groups=len(journal),vectors=3));print('TYPED SOURCE FORECASTS SEALED',case,method,flush=True)
  assert len(summaries)==18 and len(manifest)==54 and all(sha(path)==h for path,h in bindings.items())
  with (d/'vector_manifest.json').open('x') as stream:json.dump(manifest,stream,indent=2)
  bindings[str(d/'vector_manifest.json')]=sha(d/'vector_manifest.json')
  with (d/'receipt.json').open('x') as stream:json.dump(dict(status='all54_source_only_type_consistent_risk_vectors_materialized',bindings=bindings,summaries=summaries,groups=len(groups),IPIN_groups=sum(g['kind']=='direct_sink_IPIN' for g in groups),positive_RR_nodes=len(positive),scope='Exact group expectation under independent uniform NET-choice prior, complete NET unique ownership and explicit deterministic fallback. No target pressure values read, new forecast score outcomes, native run, path commit or primary-gate promotion. Independent real-graph/vector audit remains pending.'),stream,indent=2)

if __name__=='__main__':main()
