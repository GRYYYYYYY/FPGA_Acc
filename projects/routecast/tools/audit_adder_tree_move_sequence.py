"""Consecutive moves: retain live ledger/cache and compare each step to full search."""
import collections,json,shutil,subprocess,time
from pathlib import Path
from types import SimpleNamespace
from pre_route_endpoints import sha
from prepared_csr import read
from affected_connections import affected
from rr_local_batch_occupancy import LocalBatchOccupancy
from streaming_prediction_audit import Nodes,Edges,verify
from incremental_channel_pressure import ChannelPressure
from connection_golden import Result


def main():
 base=Path('experiments');design='adder_tree_2L_032bits';sequence=base/'adder_tree_2L032_move_sequence_2026-10-06';baseline=base/'adder_tree_family_predictions_2026-10-06'/design/'sparse_reset';front=base/'adder_tree_family_endpoints_2026-10-06'/design;prepared=base/'adder_tree_family_length_switch_csr_2026-10-06'/design
 out=base/'adder_tree_2L032_move_sequence_audit_2026-10-06';out.mkdir();bindings={}
 def load(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
 sr=load(sequence/'receipt.json');sp=load(sequence/'protocol.json');assert sr['protocol_sha256']==sha(sequence/'protocol.json');assert all(sha(v['path'])==v['sha256'] for v in sp['inputs'].values())
 before=load(front/'endpoints.json');fr=load(front/'receipt.json');assert sha(front/'endpoints.json')==fr['outputs']['endpoints.json']
 active=load(baseline/'prediction.json');br=load(baseline/'receipt.json');bp=load(baseline/'protocol.json');assert sha(baseline/'prediction.json')==br['prediction_sha256'] and sha(baseline/'protocol.json')==br['protocol_sha256']
 binary=Path('build/routecast_csr_authenticated_sparse_reset');assert sha(binary)==bp['binary_sha256'];bindings[str(binary)]=sha(binary)
 m,f=read(prepared/'csr',before['graph_sha256']);assert sha(prepared/'csr/manifest.json')==bp['csr_manifest_sha256'];slots=[0]*m['edges'];edges={}
 for node in range(m['nodes']):
  for slot in range(f['row_offsets'][node],f['row_offsets'][node+1]):
   eid=f['edge_ids'][slot];slots[eid]=slot;edges[eid]=SimpleNamespace(source=node,sink=f['dest_ranks'][slot],switch_id=f['switch_ids'][slot])
 graph=SimpleNamespace(nodes=Nodes(f['types'],f['capacities']),edges=Edges(edges,m['edges']));ledger=LocalBatchOccupancy(graph)
 def req(row,epoch):return {k:row[k] for k in ('connection_id','net_id','source','sink')}|{'epoch':epoch,'edge_ids':row['physical_edge_ids']}
 assert ledger.update_batch([req(r,1) for r in active['connections']])==Result.COMMITTED
 cache=ChannelPressure(f['types'],f['capacities']);cache.refresh(ledger._occupancy,range(m['nodes']))
 def search(rows,tag):
  start=time.monotonic();groups=collections.defaultdict(list);result_rows=[]
  for row in rows:groups[row['net_id']].append(row)
  with (out/(tag+'_stderr.log')).open('w') as error:
   worker=subprocess.Popen([str(binary.resolve()),str((prepared/'csr').resolve()),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error,text=True)
   try:
    for net,group in sorted(groups.items()):
     source=group[0]['source'];assert all(r['source']==source for r in group);sinks=sorted({r['sink'] for r in group});worker.stdin.write(' '.join(map(str,[source,*sinks]))+'\n');worker.stdin.flush();result=json.loads(worker.stdout.readline());assert not result['budget_exhausted']
     for row in group:result_rows.append({**row,'physical_edge_ids':result['paths'][str(row['sink'])],'method':'sparse_reset'})
    worker.stdin.close();assert worker.wait(timeout=30)==0
   finally:
    if worker.poll() is None:worker.terminate();worker.wait()
  return result_rows,time.monotonic()-start
 results=[]
 for step in sr['steps']:
  i=step['step'];assert all(sha(sequence/name)==digest for name,digest in step['outputs_sha256'].items());after=load(sequence/f'step_{i}_endpoints.json');closure=affected(before,after);assert closure==load(sequence/f'step_{i}_closure.json');selected=set(closure['recompute_connection_ids'])
  partial,partial_s=search([r for r in after['connections'] if r['connection_id'] in selected],f'{i}_partial');full,full_s=search(after['connections'],f'{i}_full');full.sort(key=lambda r:r['connection_id']);merged=sorted([r for r in active['connections'] if r['connection_id'] not in selected]+partial,key=lambda r:r['connection_id']);assert merged==full
  dirty=set()
  for row in partial:
   dirty.update(ledger._states[row['connection_id']][1].nodes);node=row['source'];dirty.add(node)
   for eid in row['physical_edge_ids']:node=f['dest_ranks'][slots[eid]];dirty.add(node)
  start=time.monotonic();assert ledger.update_batch([req(r,i+1) for r in partial])==Result.COMMITTED;cache.refresh(ledger._occupancy,dirty);payload=cache.payload(before['graph_sha256']);update_s=time.monotonic()-start
  union=collections.defaultdict(set)
  for row in full:
   node=row['source'];union[row['net_id']].add(node)
   for eid in row['physical_edge_ids']:node=f['dest_ranks'][slots[eid]];union[row['net_id']].add(node)
  occupancy=collections.Counter(n for nodes in union.values() for n in nodes);assert dict(occupancy)=={n:v for n,v in ledger._occupancy.items() if v}
  rebuilt=ChannelPressure(f['types'],f['capacities']);rebuilt.refresh(occupancy,range(m['nodes']));assert payload==rebuilt.payload(before['graph_sha256'])
  prediction={'physical_graph_sha256':before['graph_sha256'],'connections':merged,'node_occupancy':{str(n):v for n,v in occupancy.items()},'requested':len(merged),'completed':len(merged),'methods':{'sparse_reset':len(merged)}}
  physical=verify(sp['inputs']['rr_graph']['path'],after,prediction);assert physical['all_physical_and_union_checks_passed']
  (out/f'step_{i}_prediction.json').write_text(json.dumps(prediction)+'\n');(out/f'step_{i}.pressure').write_text(payload);(out/f'step_{i}_physical.json').write_text(json.dumps(physical)+'\n')
  item={'step':i,'recomputed':len(partial),'retained':len(merged)-len(partial),'dirty_nodes':len(dirty),'partial_search_s':partial_s,'full_search_s':full_s,'ledger_pressure_export_s':update_s,'full_path_occupancy_pressure_exact':True,'prediction_sha256':sha(out/f'step_{i}_prediction.json'),'pressure_sha256':sha(out/f'step_{i}.pressure'),'physical_sha256':sha(out/f'step_{i}_physical.json')};results.append(item);print(json.dumps(item),flush=True);active=prediction;before=after
 assert all(sha(path)==digest for path,digest in bindings.items())
 shutil.copyfile(__file__,out/'source.py');(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(__file__),'steps':results,'scope':'Consecutive real swaps, persistent occupancy/pressure with no baseline reset, each step independently full search and originalXML audited. Development phase timings only; native QoR/end-to-end benefit/unseen family unproven.'},indent=2)+'\n')

if __name__=='__main__':main()
