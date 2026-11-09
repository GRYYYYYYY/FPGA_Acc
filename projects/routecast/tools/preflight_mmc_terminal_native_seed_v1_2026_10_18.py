"""Source-only boundary preflight; exact archived selector and independent replay."""
import json,sys,ast
from pathlib import Path
from collections import Counter,defaultdict
from array import array
from types import SimpleNamespace
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 proof=R/'experiments/mmc_terminal_commit_replay_v1_2026-10-18/verification.json';v=json.loads(proof.read_text());assert v['status']=='pass'
 selector=R/'tools/select_resident_native_seed_subset_v1.py'
 bindings={**v['bindings'],str(proof):sha(proof),**closure([Path(__file__),selector])}
 inputs=json.loads((R/'experiments/mmc_terminal_batch_commit_v2_2026-10-18/protocol.json').read_text())['inputs']
 out=R/'experiments/mmc_terminal_native_seed_preflight_v1_2026-10-18';out.mkdir()
 tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For))
 begin=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec')
 end=next(i for i,n in enumerate(loop.body) if i>begin and isinstance(n,ast.Assert))
 code=compile(ast.Module(body=loop.body[begin:end],type_ignores=[]),str(selector),'exec')
 with (out/'protocol.json').open('x') as stream:
  json.dump(dict(bindings=bindings,inputs=inputs,selection='Unmodified archived completeNET selector AST: descending query count, ascending unique tree node count, numeric NET ID. Compare original retained_off with fixed admitted batch. All rejected query IDs remain required/pending.',audit='Recover archived baseline selected records/pending/decisions exactly; independently replay selected wholeNET loads and blockers from directXML capacities/destinations. No native labels used.',scope='Native seed record boundary only; not serialized native pin/nonconfigurable/canonical admission or a new native run. Changed payloads require later independent serializer audit before utility testing.'),stream,indent=2)
 cache=Cache();states={};needed=set();graphs=set();summaries=[]
 with cache.installed():
  assert all(sha(p)==h for p,h in bindings.items())
  for case,data in inputs.items():
   endpoint=json.loads(Path(data['endpoint']).read_text());graphs.add(endpoint['inputs']['graph']['path'])
   baseline=Path(data['frame']);candidate=R/'experiments/mmc_terminal_batch_commit_v2_2026-10-18'/case/'frame.json'
   old=json.loads(baseline.read_text());new=json.loads(candidate.read_text())
   for p in [baseline,candidate]:assert bindings[str(p)]==sha(p)
   assert old['required_connections']==new['required_connections']==115572
   states[case]=(endpoint,old,new)
   needed.update(e for frame in [old,new] for r in frame['records'] for e in r['answer']['physical_edge_ids'])
  assert len(graphs)==1;graph=Path(next(iter(graphs)));assert bindings[str(graph)]==sha(graph)
  capacities=array('Q');destinations={};edge_id=0;stack=[]
  for event,node in ET.iterparse(graph,events=('start','end')):
   if event=='start':stack.append(node);continue
   parent=stack[-2].tag if len(stack)>1 else None
   if node.tag=='node' and parent=='rr_nodes':
    assert int(node.get('id'))==len(capacities);capacities.append(int(node.get('capacity')))
   if node.tag=='edge' and parent=='rr_edges':
    if edge_id in needed:destinations[edge_id]=int(node.get('sink_node'))
    edge_id+=1
   stack.pop()
   if stack:stack[-1].remove(node)
   node.clear()
  assert destinations.keys()==needed
  class Nodes:
   def __getitem__(self,n):return SimpleNamespace(capacity=capacities[n])
  class Edges:
   def __getitem__(self,e):return SimpleNamespace(sink=destinations[e])
  xml=SimpleNamespace(graph=SimpleNamespace(nodes=Nodes(),edges=Edges()))
  for case,(endpoint,old,new) in states.items():
   outputs={}
   for name,frame in [('baseline',old),('candidate',new)]:
    scope=dict(c=frame,ep=endpoint,xml=xml,groups=defaultdict(list),Counter=Counter);exec(code,scope)
    allids={q['connection_id'] for q in endpoint['connections']};ids={r['connection_id'] for r in scope['records']}
    assert len(ids)==len(scope['records']) and ids.isdisjoint(scope['pending']) and ids|set(scope['pending'])==allids
    # Independent plain-dict replay, without consuming producer owner sets/order.
    groups=defaultdict(list)
    for r in frame['records']:groups[r['net_id']].append(r)
    owns={net:{r['source'] for r in rs}|{destinations[e] for r in rs for e in r['answer']['physical_edge_ids']} for net,rs in groups.items()}
    order=sorted(groups,key=lambda net:(-len(groups[net]),len(owns[net]),net));loads={};decisions=[];kept=[]
    for net in order:
     blockers=sorted(p for p in owns[net] if loads.get(p,0)>=capacities[p])
     decisions.append(dict(net_id=net,admitted=not blockers,blocking_nodes=blockers))
     if not blockers:
      kept.append(net)
      for p in owns[net]:loads[p]=loads.get(p,0)+1
    assert decisions==scope['decisions'] and kept==scope['kept'] and loads==dict(scope['ledger'])
    assert all(n<=capacities[p] for p,n in loads.items())
    outputs[name]=dict(records=scope['records'],pending=scope['pending'],decisions=scope['decisions'],kept=kept)
   archive=R/'experiments/mmc_v2_native_seed_inputs_v1_2026-10-18'/case/'retained_off'
   archived=archive/'subset.json';receipt=archive/'receipt.json';rp=json.loads(receipt.read_text())
   assert rp['complete_partition_and_capacity_pass'] and rp['bindings'][str(archived)]==sha(archived)
   bindings[str(receipt)]=sha(receipt);bindings[str(archived)]=sha(archived)
   assert {k:outputs['baseline'][k] for k in ['records','pending','decisions']}==json.loads(archived.read_text())
   baseline={r['connection_id']:r for r in outputs['baseline']['records']};candidate={r['connection_id']:r for r in outputs['candidate']['records']}
   originals={r['connection_id']:r for r in old['records']};changed={r['connection_id'] for r in new['records'] if r!=originals[r['connection_id']]}
   summary=dict(case=case,baseline_selected_queries=len(baseline),candidate_selected_queries=len(candidate),baseline_pending_queries=len(outputs['baseline']['pending']),candidate_pending_queries=len(outputs['candidate']['pending']),changed_input_paths=len(changed),changed_input_paths_selected=sorted(changed&candidate.keys()),changed_input_paths_pending=sorted(changed-candidate.keys()),gained_selected_NETs=sorted(set(outputs['candidate']['kept'])-set(outputs['baseline']['kept'])),lost_selected_NETs=sorted(set(outputs['baseline']['kept'])-set(outputs['candidate']['kept'])),altered_common_selected_paths=sorted(cid for cid in baseline.keys()&candidate.keys() if baseline[cid]!=candidate[cid]),selected_records_identical=outputs['baseline']['records']==outputs['candidate']['records'],pending_queries_identical=outputs['baseline']['pending']==outputs['candidate']['pending'],baseline_archived_subset_recovered_exactly=True,both_selectors_independently_replayed=True)
   folder=out/case;folder.mkdir()
   with (folder/'candidate_subset.json').open('x') as stream:json.dump({k:outputs['candidate'][k] for k in ['records','pending','decisions']},stream)
   with (folder/'comparison.json').open('x') as stream:json.dump(summary,stream,indent=2)
   summaries.append(summary);print(json.dumps(summary),flush=True)
  assert all(sha(p)==h for p,h in bindings.items())
  bindings.update({str(p):sha(p) for p in out.rglob('*.json')})
  with (out/'receipt.json').open('x') as stream:json.dump(dict(status='all3_native_seed_record_boundary_preflight_pass',bindings=bindings,summaries=summaries,RR_nodes=len(capacities),physical_edges_scanned=edge_id,scope='Source-only fixed selector comparison. Exact old archive recovery, full selected/pending partition and independent capacity replay. New candidate native route serialization/import/utility remains untested.'),stream,indent=2)

if __name__=='__main__':main()
