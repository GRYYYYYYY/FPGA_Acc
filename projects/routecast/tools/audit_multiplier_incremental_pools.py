"""Real-move dirty path unions versus independent full pooled producer."""
import json,shutil,time
from pathlib import Path
from pre_route_endpoints import sha
from prepared_csr import read
from pooled_channel_pressure import rows,payload
from incremental_pooled_pressure import PooledPressure

base=Path('experiments');out=base/'multiplier_incremental_pools_2026-10-06';out.mkdir();(out/'source').mkdir();bindings={};results=[]
def load(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
for name in ('audit_multiplier_incremental_pools.py','incremental_pooled_pressure.py','pooled_channel_pressure.py','prepared_csr.py','pre_route_endpoints.py'):
 shutil.copyfile(Path('tools')/name,out/'source'/name);bindings[str(Path('tools')/name)]=sha(Path('tools')/name)
for w in range(4,10):
 d=f'mult_{w}x{w}';oldroot=base/'multiplier_family_predictions_2026-10-06'/d/'sparse_reset';newroot=base/'multiplier_moved_incremental_search_2026-10-06'/d;pooled=base/'multiplier_pooled_pressure_2026-10-06'/d
 old=load(oldroot/'prediction.json');br=load(oldroot/'receipt.json');new=load(newroot/'prediction.json');nr=load(newroot/'receipt.json');pr=load(pooled/'receipt.json');assert sha(oldroot/'prediction.json')==br['prediction_sha256'] and sha(newroot/'prediction.json')==nr['prediction_sha256'];assert nr['paths_equal_full_moved_search'] and all(sha(p)==h for p,h in nr['inputs_sha256'].items())
 graph=old['physical_graph_sha256'];prepared=base/'multiplier_family_length_switch_csr_2026-10-06'/d;cr=load(prepared/'receipt.json');assert sha(prepared/'csr/manifest.json')==cr['manifest_sha256'];m,f=read(prepared/'csr',graph);slots=[0]*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 selected=set(nr['closure']['recompute_connection_ids']);dirty=set()
 for prediction in (old,new):
  for row in prediction['connections']:
   if row['connection_id'] not in selected:continue
   node=row['source'];dirty.add(node)
   for eid in row['physical_edge_ids']:
    slot=slots[eid];assert f['row_offsets'][node]<=slot<f['row_offsets'][node+1];node=f['dest_ranks'][slot];dirty.add(node)
   assert node==row['sink']
 oldocc={int(n):v for n,v in old['node_occupancy'].items()};newocc={int(n):v for n,v in new['node_occupancy'].items()};cache=PooledPressure(f);cache.refresh(oldocc,range(m['nodes']));original=cache.payload(graph)
 start=time.monotonic();stats=cache.refresh(newocc,dirty);refresh_s=time.monotonic()-start;start=time.monotonic();export=cache.payload(graph);serialize_s=time.monotonic()-start
 independent=payload(m['nodes'],graph,rows(f,newocc)[0]);assert export==independent and export==(pooled/'candidate.pressure').read_text() and sha(pooled/'candidate.pressure')==pr['pressure_sha256']['candidate.pressure'];bindings[str(pooled/'candidate.pressure')]=sha(pooled/'candidate.pressure')
 before=(dict(cache.rows),dict(cache.node_excess),dict(cache.group_excess))
 try:cache.refresh(newocc,[next(iter(dirty)),-1])
 except ValueError:pass
 else:raise AssertionError('invalid dirty accepted')
 assert (cache.rows,cache.node_excess,cache.group_excess)==before
 cache.refresh(oldocc,dirty);assert cache.payload(graph)==original
 result={'design':d,'recomputed_connections':len(selected),'dirty_path_nodes':len(dirty),**stats,'refresh_s':refresh_s,'serialize_s':serialize_s,'full_and_archived_payload_byte_exact':True,'invalid_refresh_preserves_all_cache_state':True,'rollback_payload_exact':True};results.append(result);print(json.dumps(result),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(out/'report.json').write_text(json.dumps({'inputs_sha256':bindings,'results':results,'scope':'Dirty union comes from both old/new affected physical paths; frozen pool metadata, integer excess, all affected group members refreshed. Cache validation before publication; no joint ledger/cache API or full pipeline cost/benefit yet. Initialization, graph/auth/search and native excluded from local phase timings.'},indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'all_six_pass':True},indent=2)+'\n')
