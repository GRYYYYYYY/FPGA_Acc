"""Freeze and materialize label-free, mass-conserving channel forecasts."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 old=R/'experiments/mmc_terminal_batch_quality_v1_2026-10-18'
 evidence=old/'research_decision_v1.json';v=json.loads(evidence.read_text());assert v['status']=='all108_terminal_batch_metric_vectors_independently_verified'
 bindings={**v['bindings'],str(evidence):sha(evidence),**closure([Path(__file__)])}
 inputs={case:json.loads((old/case/'protocol.json').read_text()) for case in ['case_01','case_02','case_03']}
 methods=list(inputs['case_01']['predictions']);assert len(methods)==6
 d=R/'experiments/mmc_geometry_pool_forecasts_v1_2026-10-18';d.mkdir()
 with (d/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=inputs,source_methods=methods,primary_candidate='pooled_native_retained_on',primary_controls=['native_retained_on','raw_min_on','previous_native'],primary_label='cold',supplemental_labels=['partial_seed_default','partial_seed_firstpass_preserve'],grouping='Positive-capacity CHANX/CHANY only; key=(type,direction,all loc attributes except ptc with default layer0,all segment attributes,all timing attributes). Node ID and track ptc excluded. No demand/target-label dependent membership.',projection='Group density=sum original member occupancy / sum original member capacity. Per-node forecast=capacity*density. Do not clip overload or discard zero-demand groups. Group mass and spatial-bin mass conserved exactly.',gates='Original full domains, metrics, ties and all3-case nonregression+strict comparison rule; unchanged3controls. All6source projections are reported, primary fixed before transformed outcomes.',scope='Development-only density forecast, not an integral path ledger, graph automorphism, native-equivalent resources or native handoff state. No target label is used to construct forecasts.'),stream,indent=2)
 cache=Cache();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  endpoints=[json.loads(Path(p['endpoint']).read_text()) for p in inputs.values()]
  graphs={p['inputs']['graph']['path'] for p in endpoints};assert len(graphs)==1
  graph=Path(next(iter(graphs)));assert bindings[str(graph)]==sha(graph)
  groups=[];lookup={};stack=[];channels=0
  for event,node in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(node);continue
   parent=stack[-2].tag if len(stack)>1 else None
   if node.tag=='node' and parent=='rr_nodes':
    kind=node.get('type');cap=int(node.get('capacity'))
    if kind in ('CHANX','CHANY') and cap>0:
     loc=dict(node.find('loc').attrib);loc.pop('ptc',None);loc.setdefault('layer','0')
     segment=node.find('segment');timing=node.find('timing')
     key=(kind,node.get('direction'),tuple(sorted(loc.items())),tuple(sorted(segment.attrib.items())) if segment is not None else (),tuple(sorted(timing.attrib.items())) if timing is not None else ())
     if key not in lookup:lookup[key]=len(groups);groups.append(dict(key=key,members=[],capacity=0))
     g=groups[lookup[key]];g['members'].append([int(node.get('id')),cap]);g['capacity']+=cap;channels+=1
    stack[-2].remove(node);node.clear()
   if node.tag=='rr_nodes':break
   stack.pop()
  assert channels==258720
  inventory=d/'groups.json'
  with inventory.open('x') as stream:json.dump(dict(graph_sha256=sha(graph),channels=channels,groups=groups),stream)
  bindings[str(inventory)]=sha(inventory)
  print('FROZEN GEOMETRY GROUPS',len(groups),'channels',channels,flush=True)
  for case,p in inputs.items():
   masses={};source_hashes={}
   for method,path in p['predictions'].items():
    path=Path(path);assert bindings[str(path)]==sha(path);frame=json.loads(path.read_text());assert frame['required_connections']==frame['completed_connections']==115572
    ledger={int(n):value for n,value in frame['ledger'].items()};assert all(type(value) is int and value>=0 for value in ledger.values())
    masses[method]=[sum(ledger.get(n,0) for n,cap in group['members']) for group in groups];source_hashes[method]=sha(path)
   target=d/(case+'.json')
   with target.open('x') as stream:json.dump(dict(schema='ROUTECAST_GEOMETRY_POOLED_DENSITY_V1',case=case,source_hashes=source_hashes,group_inventory_sha256=sha(inventory),group_demand_numerators=masses,denominators='groups.json capacity per group',scope='Rational density forecast only; no paths, integer ledger or native admissibility claimed.'),stream)
   bindings[str(target)]=sha(target);summaries.append(dict(case=case,groups=len(groups),forecasts=len(masses)))
   print('LABEL-FREE FORECASTS SEALED',case,flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  with (d/'receipt.json').open('x') as stream:json.dump(dict(status='all18_source_only_forecasts_materialized_before_transformed_metrics',bindings=bindings,summaries=summaries,scope='Group partition fixed from graph; density masses read source frames only. No transformed target metric read or used, no native run or path commit.'),stream,indent=2)

if __name__=='__main__':main()
