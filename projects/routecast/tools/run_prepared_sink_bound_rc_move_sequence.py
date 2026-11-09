"""Actual consecutive placements: lower-bound endpoint-only cache hazards."""
import json,heapq,time,os
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read,TYPES
from affected_connections import affected
from pre_route_endpoints import sha
from cost_read_dependency_index import CostReadDependencyIndex
from dynamic_net_dijkstra import search as net_search
from csr_integer_budget_search import query
from native_integer_rc_prepared_sink_bound import NativeIntegerRCPreparedSinkBound
from prepared_rc_sink_bounds import PreparedRCSinkBounds
from rc_read_dependency_cache_direct_restore import DirectRestoreRCReadDependencyCache as RCReadDependencyCache
from net_occupancy_delta import replace_net
from csr_exact_buffered_rc import ExactBufferedRC
from buffered_rc_context import load as load_rc
from integer_rc_context import IntegerRC
from prepared_integer_rc_context import PreparedIntegerRC
from streaming_prediction_audit import verify
from immutable_xml_prediction_audit import ImmutableXMLAudit
from move_prediction_transaction import MoveState,MovePredictionTransaction
from incremental_channel_pressure import ChannelPressure
import hashlib


def main():
 root=Path(__file__).resolve().parents[1];base=root/'experiments'
 sequence=base/'adder_tree_2L032_move_sequence_2026-10-06'
 audit=base/'adder_tree_2L032_move_sequence_audit_2026-10-06'
 out=Path(os.environ['ROUTECAST_TRANSACTION_OUTPUT']);assert out.resolve().parent==(root/'experiments').resolve();out.mkdir()
 (out/'sources').mkdir()
 import shutil
 names=['prepared_rc_sink_bounds.py','native_integer_rc_prepared_sink_bound.py','native_integer_rc_sink_bound.py','native_integer_rc_delta_search.py','prepared_integer_rc_context.py','native_integer_rc_delta_demand.py','rc_read_dependency_cache_direct_restore.py','rc_read_dependency_cache.py','native_integer_rc_sparse_trace.py','immutable_xml_prediction_audit.py','net_occupancy_delta.py','native_integer_rc_search.py','move_prediction_transaction.py','incremental_channel_pressure.py','run_prepared_sink_bound_rc_move_sequence.py','csr_integer_budget_search.py','integer_rc_context.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','streaming_prediction_audit.py','physical_prediction_audit.py','net_union_topology.py','pre_route_endpoints.py']
 for n in names:shutil.copyfile(root/'tools'/n,out/'sources'/n)
 sources={n:sha(out/'sources'/n) for n in names}
 bindings={}
 def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
 sr=load(sequence/'receipt.json');ar=load(audit/'receipt.json')
 endpoints=load(base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json')
 pred=load(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json')
 br=load(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/receipt.json');assert sha(base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json')==br['prediction_sha256']
 m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',endpoints['graph_sha256'])
 slots={f['edge_ids'][i]:(u,i) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 def state(p):
  unions=defaultdict(set)
  for r in p['connections']:
   unions[r['net_id']].add(r['source'])
   for e in r['physical_edge_ids']:
    u,i=slots[e];unions[r['net_id']].update((u,f['dest_ranks'][i]))
  occ=Counter(n for nodes in unions.values() for n in nodes)
  assert +occ==Counter({int(n):v for n,v in p['node_occupancy'].items()})
  return unions,occ
 sp=load(sequence/'protocol.json');assert sr['protocol_sha256']==sha(sequence/'protocol.json')
 for value in sp['inputs'].values():assert sha(value['path'])==value['sha256']
 xml_audit=ImmutableXMLAudit(sp['inputs']['rr_graph']['path'],sp['inputs']['rr_graph']['sha256'])
 budget_root=base/'adder_tree_online_move_rc_budgets_2026-10-06';budget_receipt=load(budget_root/'receipt.json')
 rc=PreparedIntegerRC(ExactBufferedRC(f,*load_rc(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits',endpoints['graph_sha256'])),base/'adder_tree_prepared_integer_rc_2026-10-06','7f8ce091f40c8f7f0f879a068293f20c76be9ebbbb3c0371462eca0f0724e617')
 for p in (base/'adder_tree_prepared_integer_rc_2026-10-06').iterdir():
  if p.is_file():bindings[str(p)]=sha(p)
 assert rc.scale==budget_receipt['integer_scale']
 bounds=PreparedRCSinkBounds(base/'adder_tree_prepared_rc_sink_bounds_2026-10-06','dadcaee7761667b995ab9b37b6fa15b00529dddc8af7fd61ebdf13a9ab19d167',endpoints['graph_sha256'],rc.scale,m['nodes']);native=NativeIntegerRCPreparedSinkBound(rc,bounds)
 for p in (base/'adder_tree_prepared_rc_sink_bounds_2026-10-06').glob('*.bin'):bindings[str(p)]=sha(p)
 bindings[str(base/'adder_tree_prepared_rc_sink_bounds_2026-10-06/receipt.json')]=sha(base/'adder_tree_prepared_rc_sink_bounds_2026-10-06/receipt.json')
 bindings[str(root/'build/rc_budget_native_sink_bound_2026-10-06/search.so')]=sha(root/'build/rc_budget_native_sink_bound_2026-10-06/search.so')
 bindings[str(root/'build/rc_budget_native_2026-10-06/search.so')]=sha(root/'build/rc_budget_native_2026-10-06/search.so');bindings[str(root/'tools/rc_budget_native/search.cpp')]=sha(root/'tools/rc_budget_native/search.cpp')
 overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items())
 for p in (root/'build/rc_budget_native_sparse_trace_2026-10-06/search.so',root/'tools/rc_budget_native_sparse_trace/search.cpp'):bindings[str(p)]=sha(p)
 def stage(old,step,fault=None):
  dependency_cache=RCReadDependencyCache.restore(m['nodes'],old.search_cache);cache_hits=0;cache_misses=0;demand_writes=0
  previous_other={n:int(native.other[n]) for n in native.previous}
  previous=json.loads(old.prediction);unions,occ=state(previous);active={r['connection_id']:r for r in previous['connections']};endpoints=json.loads(old.endpoints);epoch=old.epoch*385
  start=time.monotonic()
  if step:
   detail=sr['steps'][step-1];assert all(sha(sequence/n)==h for n,h in detail['outputs_sha256'].items())
   endpoints=load(sequence/f'step_{step}_endpoints.json')
  groups=defaultdict(list)
  for row in endpoints['connections']:groups[row['net_id']].append(row)
  budgetfile=budget_root/f'step_{step}_budgets.json';assert sha(budgetfile)==budget_receipt['steps'][step]['budget_sha256'];budgets={r['connection_id']:r['scaled_integer_budget'] for r in load(budgetfile)}
  reference_file=base/'adder_tree_family_predictions_2026-10-06/adder_tree_2L_032bits/sparse_reset/prediction.json' if step==0 else audit/f'step_{step}_prediction.json'
  assert sha(reference_file)==budget_receipt['steps'][step]['reference_prediction_sha256'];reference={r['connection_id']:r for r in load(reference_file)['connections']};restored=[]
  # Restore complete NETs only when new endpoints/budgets invalidate old witnesses.
  for net,rows in sorted(groups.items()):
   if any(any(active[r['connection_id']][key]!=r[key] for key in ('net_id','source','sink')) or rc.path(r['source'],r['sink'],active[r['connection_id']]['physical_edge_ids'])>budgets[r['connection_id']] for r in rows):
    restored.append(net)
    for r in rows:active[r['connection_id']]=reference[r['connection_id']]
  unions=defaultdict(set)
  for r in active.values():
   unions[r['net_id']].add(r['source'])
   for eid in r['physical_edge_ids']:
    u,i=slots[eid];unions[r['net_id']].update((u,f['dest_ranks'][i]))
  occ=Counter(n for nodes in unions.values() for n in nodes)
  initial_overflow=overflow(occ);current_overflow=initial_overflow;journal=[];query_count=0
  if fault=='after_repairs':raise RuntimeError('injected after repairs')
  for net,rows in sorted(groups.items()):
   source=rows[0]['source'];assert all(r['source']==source for r in rows)
   other=occ.copy();other.subtract(unions[net])
   captured_other={n:v for n,v in other.items() if v}
   updates=[(n,captured_other.get(n,0)) for n in previous_other.keys()|captured_other.keys() if previous_other.get(n,0)!=captured_other.get(n,0)]
   native.apply_other(native.demand_epoch,updates);demand_writes+=len(updates);previous_other=captured_other
   result={};examined=0;statuses={}
   for r in rows:
    found=native.query(source,r['sink'],budgets[r['connection_id']],10000);cache_misses+=1
    query_count+=1
    if fault=='during_search' and query_count==20:raise RuntimeError('injected after 20 real queries')
    result[r['connection_id']]=(found['status'],found['cost'],found['physical_edge_ids']);examined+=found['examined_edges'];statuses[r['connection_id']]=found['status']
   candidates={};newunion={source};records=[];allfound=True
   for row in rows:
    status,cost,path=result[row['connection_id']]
    if status!='FOUND':allfound=False;continue
    assert rc.path(source,row['sink'],path)<=budgets[row['connection_id']]
    node=source;objective=0;seen={node}
    for eid in path:
     u,i=slots[eid];assert u==node;node=f['dest_ranks'][i];assert node not in seen;seen.add(node)
     objective+=int(f['costs'][i])*(1+occ[node]-(node in unions[net]))
    assert node==row['sink'] and objective==cost
    newunion.update(seen);candidates[row['connection_id']]={**row,'physical_edge_ids':list(path),'method':'online_dynamic_net'}
    records.append({'connection_id':row['connection_id'],'cost_at_search_epoch':cost,'physical_edge_ids':path})
   before=current_overflow;accepted=False;candidate_overflow=None;tree_ok=True
   if allfound:
    unique={eid for r in candidates.values() for eid in r['physical_edge_ids']};incoming=Counter();outgoing=defaultdict(list)
    for eid in unique:
     u,i=slots[eid];v=f['dest_ranks'][i];incoming[v]+=1;outgoing[u].append(v)
    tree_ok=not incoming[source] and all(v<=1 or f['types'][n]==TYPES['SINK'] for n,v in incoming.items())
    degree={n:incoming[n] for n in newunion};queue=[n for n in newunion if degree[n]==0];visited=0
    while queue:
     n=queue.pop();visited+=1
     for v in outgoing[n]:
      degree[v]-=1
      if degree[v]==0:queue.append(v)
    tree_ok=tree_ok and visited==len(newunion)
    staged,candidate_overflow,dirty=replace_net(occ,unions[net],newunion,f['capacities'],current_overflow)
    if tree_ok and candidate_overflow<=before:
     active.update(candidates);unions[net]=newunion;occ=staged;current_overflow=candidate_overflow;accepted=True
   epoch+=1
   journal.append({'epoch':epoch,'net_id':net,'statuses':statuses,'accepted':accepted,'tree_ok':tree_ok,'connections':records,'before_overflow':before,'candidate_overflow':candidate_overflow,'after_overflow':current_overflow,'examined_edges':examined})
  if fault=='after_search':raise RuntimeError('injected after search')
  prediction={'physical_graph_sha256':endpoints['graph_sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':{'online_dynamic_net':len(active)}}
  for r in prediction['connections']:assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])<=budgets[r['connection_id']]
  assert current_overflow==overflow(occ)
  rebuilt_u,rebuilt_o=state(prediction);assert dict(rebuilt_u)==dict(unions) and +occ==rebuilt_o
  physical=xml_audit.verify(endpoints,prediction,topology=True);assert physical['all_physical_and_union_checks_passed'];assert physical['all_type_overuse_units']==overflow(occ)
  if fault=='after_audit':raise RuntimeError('injected after audit')
  pressure=ChannelPressure(f['types'],f['capacities']);pressure.refresh(occ,range(m['nodes']));payload=pressure.payload(endpoints['graph_sha256']).encode()
  if fault=='after_pressure':raise RuntimeError('injected after pressure serialization')
  cache_payload=dependency_cache.payload()
  if fault=='after_cache':raise RuntimeError('injected after cache serialization')
  candidate=MoveState(old.epoch+1,old.context,(sequence/f'step_{step}.place').read_bytes(),(sequence/f'step_{step}_endpoints.json').read_bytes(),(json.dumps(prediction)+'\n').encode(),budgetfile.read_bytes(),payload,cache_payload)
  return candidate,{'step':step,'restored_nets':len(restored),'final_overflow':overflow(occ),'queries':query_count,'demand_node_writes':demand_writes,'cache_hits':cache_hits,'cache_misses':cache_misses,'cache_payload_bytes':len(cache_payload),'journal':journal,'physical':physical,'wall_s':time.monotonic()-start}
 parent=base/'adder_tree_online_rc_budget_net_sequence_v2_2026-10-06';prior=load(parent/'receipt.json');verified=load(parent/'verification.json');assert sha(parent/'receipt.json')==verified['receipt_sha256']
 initial_prediction=parent/'step_0_prediction.json';assert sha(initial_prediction)==prior['steps'][0]['prediction_sha256'];initial=json.loads(initial_prediction.read_text());initial_pressure=ChannelPressure(f['types'],f['capacities']);initial_pressure.refresh(Counter({int(n):v for n,v in initial['node_occupancy'].items()}),range(m['nodes']))
 context=hashlib.sha256((endpoints['graph_sha256']+sha(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr/manifest.json')+sha(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits/receipt.json')+sha(root/'build/rc_budget_native_sparse_trace_2026-10-06/search.so')+sha(root/'tools/native_integer_rc_sparse_trace.py')+sha(root/'tools/native_integer_rc_delta_demand.py')+sha(root/'tools/native_integer_rc_delta_search.py')+sha(root/'build/rc_budget_native_sink_bound_2026-10-06/search.so')+sha(root/'tools/native_integer_rc_prepared_sink_bound.py')+sha(base/'adder_tree_prepared_rc_sink_bounds_2026-10-06/receipt.json')+sha(root/'tools/prepared_integer_rc_context.py')+sha(root/'tools/rc_read_dependency_cache.py')+sha(root/'tools/rc_read_dependency_cache_direct_restore.py')).encode()).hexdigest()
 old=MoveState(0,context,Path(sp['inputs']['reference_place']['path']).read_bytes(),json.dumps(endpoints).encode(),initial_prediction.read_bytes(),(budget_root/'step_0_budgets.json').read_bytes(),initial_pressure.payload(endpoints['graph_sha256']).encode());tx=MovePredictionTransaction(old);reports=[]
 def validate(candidate):
  restored_cache=RCReadDependencyCache.restore(m['nodes'],candidate.search_cache);assert restored_cache.payload()==candidate.search_cache
  prediction=json.loads(candidate.prediction);ep=json.loads(candidate.endpoints);budgets={r['connection_id']:r for r in json.loads(candidate.budgets)};rows={r['connection_id']:r for r in prediction['connections']};assert set(rows)==set(budgets)=={r['connection_id'] for r in ep['connections']}
  for r in ep['connections']:
   actual=rows[r['connection_id']];assert all(r[k]==actual[k] for k in ('net_id','source','sink'));assert rc.path(r['source'],r['sink'],actual['physical_edge_ids'])<=budgets[r['connection_id']]['scaled_integer_budget']
  union,occupancy=state(prediction);cache=ChannelPressure(f['types'],f['capacities']);cache.refresh(occupancy,range(m['nodes']));assert candidate.pressure==cache.payload(ep['graph_sha256']).encode();return True
 for step in range(1,4):
  old=tx.snapshot();failures=[]
  if step==int(os.environ.get('ROUTECAST_FAILURE_STEP','1')) and os.environ.get('ROUTECAST_INJECT_FAILURES')=='1':
   for phase in ('after_repairs','during_search','after_search','after_audit','after_pressure','after_cache'):
    status=tx.commit(old.epoch,lambda current:stage(current,step,phase)[0],validate);assert status=='FAILED' and tx.snapshot() is old;failures.append(phase);print(json.dumps({'step':step,'fault':phase,'previous_joint_snapshot_preserved':True}),flush=True)
  captured={}
  def build(current):
   candidate,metadata=stage(current,step);captured.update(metadata);return candidate
  assert tx.commit(old.epoch,build,validate)=='COMMITTED';current=tx.snapshot();assert current.epoch==step;assert json.loads(current.prediction)==json.loads((parent/f'step_{step}_prediction.json').read_text())
  (out/f'step_{step}_prediction.json').write_bytes(current.prediction);(out/f'step_{step}.pressure').write_bytes(current.pressure);(out/f'step_{step}_journal.json').write_text(json.dumps(captured.pop('journal'))+'\n');(out/f'step_{step}_physical.json').write_text(json.dumps(captured.pop('physical'))+'\n')
  (out/f'step_{step}_cache.json').write_bytes(current.search_cache)
  reports.append(captured|{'cache_sha256':sha(out/f'step_{step}_cache.json')}|{'failure_phases':failures,'published_epoch':current.epoch,'prediction_sha256':sha(out/f'step_{step}_prediction.json'),'pressure_sha256':sha(out/f'step_{step}.pressure'),'journal_sha256':sha(out/f'step_{step}_journal.json'),'physical_sha256':sha(out/f'step_{step}_physical.json')});print(json.dumps(reports[-1]),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());assert all(sha(root/'tools'/n)==h for n,h in sources.items())
 (out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'sources_sha256':sources,'immutable_xml_payload_bytes':xml_audit.payload_bytes,'steps':reports,'scope':'Private restored cache is part of immutable MoveState single-pointer publication; cold empty cache (no retrospective warm). Real RC search/private repair, complete NET RC/tree/capacity gate, XML audit and pressure serialization inside joint in-memory move transaction. Fault injection is optional and disabled in timing runs; separate failure audit archived. All successful predictions byte equal independently replayed prior serial experiment. Cold init excluded; no native STA, file atomicity or concurrent-reader stress.'},indent=2)+'\n')
if __name__=='__main__':main()
