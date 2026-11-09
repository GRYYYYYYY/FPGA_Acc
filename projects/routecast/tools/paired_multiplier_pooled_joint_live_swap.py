"""Two ABBA cycles of a real move, live projection/search/ledger/pressure/native."""
import collections,json,os,re,shutil,subprocess,time
from pathlib import Path
from types import SimpleNamespace
from affected_connections import affected
from prepared_endpoints import PreparedEndpoints
from pre_route_endpoints import sha
from prepared_csr import read
from rr_local_batch_occupancy import LocalBatchOccupancy
from streaming_prediction_audit import Nodes,Edges
from incremental_channel_pressure import ChannelPressure
from pooled_ledger_pressure_transaction import PooledLedgerPressureTransaction
from connection_golden import Result


def main():
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('design',choices=[f'mult_{w}x{w}' for w in range(4,10)]);args=parser.parse_args()
 base=Path('experiments');design=args.design;front=base/'multiplier_family_endpoints_2026-10-06'/design
 swap=base/'multiplier_placement_swap_2026-10-06'/design;delta=base/'multiplier_pooled_pressure_2026-10-06'/design
 baseline=base/'multiplier_family_predictions_2026-10-06'/design/'sparse_reset';prepared=base/'multiplier_family_length_switch_csr_2026-10-06'/design
 out=base/'multiplier_pooled_joint_live_swap_2026-10-06'/design;work=Path('work/multiplier_pooled_joint_live_swap_2026-10-06')/design;out.mkdir(parents=True);work.mkdir(parents=True);(out/'source').mkdir()
 start=time.monotonic();bindings={}
 def load(path):
  bindings[str(path)]=sha(path);return json.loads(path.read_text())
 fp=load(front/'protocol.json');fr=load(front/'receipt.json');assert fr['protocol_sha256']==sha(front/'protocol.json')
 inputs=fp['inputs'];assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 before=load(front/'endpoints.json');assert fr['outputs']['endpoints.json']==sha(front/'endpoints.json') and before['nonclock_global_excluded_net_ids']==[]
 old=load(baseline/'prediction.json');br=load(baseline/'receipt.json');bp=load(baseline/'protocol.json');assert br['prediction_sha256']==sha(baseline/'prediction.json') and br['protocol_sha256']==sha(baseline/'protocol.json')
 dr=load(delta/'receipt.json');payload_reference=(delta/'candidate.pressure').read_text();assert sha(delta/'candidate.pressure')==dr['pressure_sha256']['candidate.pressure'];bindings[str(delta/'candidate.pressure')]=sha(delta/'candidate.pressure')
 sr=load(swap/'receipt.json');moved_place=swap/'swapped.place';assert sha(moved_place)==sr['swapped_place_sha256'];bindings[str(moved_place)]=sha(moved_place)
 reference=load(base/'multiplier_moved_incremental_search_2026-10-06'/design/'prediction.json')
 search=Path('build/routecast_csr_authenticated_sparse_reset');assert sha(search)==bp['binary_sha256'];bindings[str(search)]=sha(search)
 build=Path('build/native_pressure_feedback_v2_2026-10-06');native=build/'routecast_pressure_vpr';nr=load(build/'receipt.json');assert sha(native)==nr['binary_sha256'];bindings[str(native)]=sha(native)
 prep=load(prepared/'receipt.json');assert prep['manifest_sha256']==sha(prepared/'csr/manifest.json')==bp['csr_manifest_sha256']
 m,f=read(prepared/'csr',inputs['rr_graph']['sha256']);slots=[0]*m['edges'];edges={}
 for node in range(m['nodes']):
  for slot in range(f['row_offsets'][node],f['row_offsets'][node+1]):
   eid=f['edge_ids'][slot];slots[eid]=slot;edges[eid]=SimpleNamespace(source=node,sink=f['dest_ranks'][slot],switch_id=f['switch_ids'][slot])
 graph=SimpleNamespace(nodes=Nodes(f['types'],f['capacities']),edges=Edges(edges,m['edges']))
 projection=PreparedEndpoints(inputs['packed_netlist']['path'],inputs['rr_graph']['path'],inputs['reference_place']['path']);assert projection.base['connections']==before['connections']
 joint=PooledLedgerPressureTransaction(graph,f,inputs['rr_graph']['sha256'])
 def req(row,epoch):return {k:row[k] for k in ('connection_id','net_id','source','sink')}|{'epoch':epoch,'edge_ids':row['physical_edge_ids']}
 assert joint.update_batch([req(r,1) for r in old['connections']])==Result.COMMITTED
 original_payload=joint.snapshot()['payload']
 error=(out/'persistent_search_stderr.log').open('w')
 worker=subprocess.Popen([str(search.resolve()),str((prepared/'csr').resolve()),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=error,text=True)
 first_net=min(r['net_id'] for r in old['connections']);seed=[r for r in old['connections'] if r['net_id']==first_net];source=seed[0]['source'];targets=sorted({r['sink'] for r in seed})
 worker.stdin.write(' '.join(map(str,[source,*targets]))+'\n');worker.stdin.flush();warm_result=json.loads(worker.stdout.readline());assert not warm_result['budget_exhausted']
 assert all(warm_result['paths'][str(r['sink'])]==r['physical_edge_ids'] for r in seed)
 (out/'worker_initialization_query.json').write_text(json.dumps({'net_id':first_net,'result':warm_result})+'\n')
 initialization_s=time.monotonic()-start
 names=['paired_multiplier_pooled_joint_live_swap.py','affected_connections.py','prepared_endpoints.py','pre_route_endpoints.py','prepared_csr.py','rr_local_batch_occupancy.py','rr_occupancy.py','incremental_channel_pressure.py','connection_golden.py','pooled_ledger_pressure_transaction.py','incremental_pooled_pressure.py','pooled_channel_pressure.py']
 for name in names:shutil.copyfile(Path('tools')/name,out/'source'/name);bindings[str(Path('tools')/name)]=sha(Path('tools')/name)
 protocol={'inputs':inputs,'bindings_sha256':bindings,'sequence':['off','on','on','off']*2,'initialization_s':initialization_s,'initialization_scope':'authenticated archived baseline prediction, graph maps/CSR/edge index, baseline ledger and pressure seed, persistent worker graph load plus authenticated seed query; initial baseline prediction production and CSR construction excluded and not amortized','scope':'Live real move warm trial with one persistent fixed-context search worker and joint ledger/pooled-pressure publication (full-state staging); on includes projection/closure/search/ledger/pressure/native and rollback-to-baseline. Off native only. Input staging and offline parity audits outside both. Concurrent host; one design, no cold/unseen/hardware claim.'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[];epoch=1
 for i,mode in enumerate(protocol['sequence']):
  tag=f'{i:02d}_{mode}';wd=work/tag;wd.mkdir()
  for key,name in [('atom','design.blif'),('packed_netlist','design.net')]:shutil.copyfile(inputs[key]['path'],wd/name)
  shutil.copyfile(moved_place,wd/'design.place');env=dict(os.environ)
  for key in ('ROUTECAST_PRESSURE_FILE','ROUTECAST_EXPECT_GRAPH_SHA256'):env.pop(key,None)
  start=time.monotonic();phases={};dirty=set();updated=[]
  if mode=='on':
   t=time.monotonic();after,_=projection.project(moved_place);closure=affected(before,after);selected=set(closure['recompute_connection_ids']);phases['projection_closure_s']=time.monotonic()-t
   t=time.monotonic();groups=collections.defaultdict(list)
   for row in after['connections']:
    if row['connection_id'] in selected:groups[row['net_id']].append(row)
   for net,group in sorted(groups.items()):
    sources={r['source'] for r in group};assert len(sources)==1;source=next(iter(sources));targets=sorted({r['sink'] for r in group})
    worker.stdin.write(' '.join(map(str,[source,*targets]))+'\n');worker.stdin.flush();result=json.loads(worker.stdout.readline());assert not result['budget_exhausted']
    for row in group:updated.append({**row,'physical_edge_ids':result['paths'][str(row['sink'])],'method':'sparse_reset'})
   phases['affected_search_s']=time.monotonic()-t
   t=time.monotonic()
   epoch+=1;assert joint.update_batch([req(r,epoch) for r in updated])==Result.COMMITTED
   payload=out/(tag+'.pressure');payload.write_text(joint.snapshot()['payload']);env['ROUTECAST_PRESSURE_FILE']=str(payload.resolve());env['ROUTECAST_EXPECT_GRAPH_SHA256']=inputs['rr_graph']['sha256'];phases['ledger_pressure_export_s']=time.monotonic()-t
  command=[str(native.resolve()),inputs['architecture']['path'],'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',inputs['rr_graph']['path'],'--route_chan_width','300','--num_workers','1','--seed','1','--max_router_iterations','100']
  (out/(tag+'_command.json')).write_text(json.dumps({'command':command,'cwd':str(wd.resolve())})+'\n');t=time.monotonic()
  with (out/(tag+'.log')).open('w') as log:code=subprocess.run(command,cwd=wd,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  phases['native_route_s']=time.monotonic()-t;assert code==0
  if mode=='on':
   t=time.monotonic();epoch+=1;assert joint.update_batch([req(r,epoch) for r in old['connections'] if r['connection_id'] in selected])==Result.COMMITTED;phases['reset_to_baseline_s']=time.monotonic()-t
  total=time.monotonic()-start
  # Offline equivalence checks deliberately follow the complete timed interval.
  if mode=='on':
   merged=sorted([r for r in old['connections'] if r['connection_id'] not in selected]+updated,key=lambda r:r['connection_id']);assert merged==sorted(reference['connections'],key=lambda r:r['connection_id'])
   assert payload.read_text()==payload_reference and joint.snapshot()['payload']==original_payload
   (out/(tag+'_connections.json')).write_text(json.dumps(merged)+'\n')
  text=(out/(tag+'.log')).read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully' in text and 'Completed placement consistency check successfully' in text
  assert ('RouteCast pressure applied' in text)==(mode=='on')
  if mode=='on':assert f'RouteCast pressure applied: {len(payload_reference.splitlines())-1} channel nodes' in text
  row={'run':i,'mode':mode,'warm_pipeline_s':total,'phases':phases,'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1]),'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),'route_sha256':sha(wd/'design.route'),'log_sha256':sha(out/(tag+'.log'))};results.append(row);print(json.dumps(row),flush=True)
 worker.stdin.close();assert worker.wait(timeout=30)==0;error.close()
 assert all(sha(p)==h for p,h in bindings.items()) and all(sha(v['path'])==v['sha256'] for v in inputs.values())
 means={}
 for mode in ('off','on'):
  group=[r for r in results if r['mode']==mode];assert len({r['route_sha256'] for r in group})==1;means[mode]=sum(r['warm_pipeline_s'] for r in group)/4
 receipt={'protocol_sha256':sha(out/'protocol.json'),'results':results,'mean_warm_pipeline_s':means,'on_over_off':means['on']/means['off'],'initialization_s':initialization_s,'live_predictions_and_payloads_exact':True,'within_mode_route_byte_repeatable':True,'scope':protocol['scope']}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'means':means,'on_over_off':receipt['on_over_off'],'initialization_s':initialization_s}),flush=True)

if __name__=='__main__':main()
