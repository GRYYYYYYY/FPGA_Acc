"""Full stereo authenticated-host implementation parity experiment, durable net-by-net journal."""
import json,time,subprocess,collections,shutil
from pathlib import Path
from array import array
from prepared_csr import read,U64
from pre_route_endpoints import sha

def run():
 prepared_name='matched_length_switch_control';endpoints_version='endpoints_undriven_v2';expected_connections=81610;total_start=time.monotonic()
 base=Path('experiments/stereo_prospective_validation_2026-10-05');prepared=base/'matched_length_switch_control';out=base/'ordinary_length_switch_prediction_undriven_v2_authenticated_host'
 if out.exists():raise ValueError('fresh output required')
 prep=json.loads((prepared/'receipt.json').read_text());p=json.loads((prepared/'protocol.json').read_text())
 assert prep['all_topology_metadata_payload_hashes_identical'] and prep['sampled_reference_Sketch_costs']==1000
 assert prep['manifest_sha256']==sha(prepared/'csr/manifest.json') and prep['protocol_sha256']==sha(prepared/'protocol.json')
 audit=json.loads((base/'streaming_csr_class_cache_v3/physical_cost_audit.json').read_text());assert audit['all_node_fields_and_raw_edges_exact']
 assert p['source_csr_manifest_sha256']==sha(base/'streaming_csr_class_cache_v3/csr/manifest.json')
 endpoint_root=base/endpoints_version
 if endpoints_version!='endpoints':
  alignment=json.loads((endpoint_root/'accounting_alignment_audit.json').read_text());assert alignment['native_retained_multiset_exact'] and alignment['all_remaining_connection_records_exact']
 ep=endpoint_root/'endpoints.json';er=json.loads((endpoint_root/'receipt.json').read_text());e=json.loads(ep.read_text())
 assert er['output_sha256']['endpoints.json']==sha(ep)
 assert len(e['connections'])==expected_connections
 inputs={**p['inputs'],'endpoints':{'path':str(ep.resolve()),'sha256':sha(ep)}}
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 binary=Path('build/routecast_csr_authenticated');dependencies={str(q):sha(q) for q in (Path(__file__),Path('tools/prepared_csr.py'),Path('tools/pre_route_endpoints.py'),Path('tools/csr_consumer/authenticated_main.cpp'),Path('tools/csr_consumer/authenticated_host_search.hpp'))};out.mkdir();(out/'source').mkdir()
 for name in dependencies:shutil.copyfile(name,out/'source'/Path(name).name)
 shutil.copy2(binary,out/'consumer');shutil.copyfile(__file__,out/'driver.py')
 protocol={'endpoints_version':endpoints_version,'frontend_protocol_sha256':sha(endpoint_root/'protocol.json'),'frontend_revision_scope':'revised frontend after native cohort defect discovery' if endpoints_version!='endpoints' else 'original frontend','prepared_artifact':prepared_name,'conversion_receipt_sha256':sha(prepared/'receipt.json'),'source_sha256':dependencies,'inputs':inputs,'binary_sha256':sha(binary),'driver_sha256':sha(__file__),'csr_manifest_sha256':prep['manifest_sha256'],'source_topology_audit_sha256':sha(base/'streaming_csr_class_cache_v3/physical_cost_audit.json'),'control_preparation_receipt_sha256':sha(prepared/'receipt.json'),'policy_sha256':sha(base/'protocol.json'),'method':'rr_length_switch existing uncalibrated control; no tuning','order':'ascending net, CID, distinct sink ID','scope':'matched cost-rule control on complete revised Stereo cohort; no native labels or tree/free-pin mechanism; not baseline implementation parity'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 assert sha(out/'consumer')==protocol['binary_sha256']
 setup_s=time.monotonic()-total_start
 start=time.monotonic();m,f=read(prepared/'csr',p['inputs']['graph']['sha256']);verify=time.monotonic()-start
 index_start=time.monotonic()
 assert all(n==i for i,n in enumerate(f['node_ids']))
 slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 groups=collections.defaultdict(list)
 for row in sorted(e['connections'],key=lambda r:(r['net_id'],r['connection_id'])):groups[row['net_id']].append(row)
 index_s=time.monotonic()-index_start
 query_start=time.monotonic()
 worker=subprocess.Popen([str((out/'consumer').resolve()),str((prepared/'csr').resolve()),'--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=(out/'consumer_stderr.log').open('w'),text=True)
 rows=[];occupancy=collections.Counter();failed=visits=settled=0
 try:
  with (out/'net_results.jsonl').open('w') as journal:
   for i,(net,cohort) in enumerate(sorted(groups.items()),1):
    sources={r['source'] for r in cohort};assert len(sources)==1;source=next(iter(sources));targets=sorted({r['sink'] for r in cohort})
    assert f['types'][source]==0 and all(f['types'][s]==1 for s in targets)
    worker.stdin.write(' '.join(map(str,[source,*targets]))+'\n');worker.stdin.flush();line=worker.stdout.readline()
    if not line:raise RuntimeError('consumer exited before net result')
    result=json.loads(line);assert not result['budget_exhausted'];assert set(result['paths'])<=set(map(str,targets))
    journal.write(json.dumps({'net_id':net,'source':source,'result':result})+'\n');journal.flush();touched=set();visits+=result['edge_visits'];settled+=result['settled_nodes']
    for row in cohort:
     path=result['paths'].get(str(row['sink']))
     if path is None:failed+=1
     else:
      node=source;seen={node}
      for eid in path:
       assert type(eid) is int and 0<=eid<m['edges'];slot=slots[eid]
       assert f['row_offsets'][node]<=slot<f['row_offsets'][node+1] and f['costs'][slot]!=U64
       node=f['dest_ranks'][slot];assert node not in seen and f['capacities'][node]>0;seen.add(node)
      assert node==row['sink'];touched.update(seen)
     rows.append({**row,'physical_edge_ids':path,'method':'rr_length_switch' if path is not None else 'failed'})
    occupancy.update(touched)
    if i%100==0:print(json.dumps({'nets':i,'total_nets':len(groups),'connections':len(rows),'failed':failed}),flush=True)
  worker.stdin.close();assert worker.wait()==0
 finally:
  if worker.poll() is None:worker.terminate();worker.wait()
 query_end=time.monotonic();query_s=query_end-query_start
 assert len(rows)==expected_connections
 assert all(sha(name)==value for name,value in dependencies.items())
 assert sha(out/'consumer')==protocol['binary_sha256'] and sha(base/'protocol.json')==protocol['policy_sha256']
 prediction={'physical_graph_sha256':p['inputs']['graph']['sha256'],'connections':rows,'node_occupancy':{str(n):v for n,v in occupancy.items()},'requested':len(rows),'completed':len(rows)-failed,'methods':dict(collections.Counter(r['method'] for r in rows))}
 (out/'prediction.json').write_text(json.dumps(prediction)+'\n')
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 receipt={'connections':len(rows),'nets':len(groups),'failed':failed,'csr_verify_s':verify,'authenticate_and_output_setup_s':setup_s,'transport_index_and_group_s':index_s,'search_ledger_s':query_s,'postprocess_and_write_s':time.monotonic()-query_end,'full_prediction_wall_s':time.monotonic()-total_start,'cold_conversion_wall_s':prep['wall_s'],'timing_scope':'full prediction driver includes authentication/indexing/consumer loading/search/ledger/output; conversion separate; upstream endpoints/native cost export/independent offline audits/feedback/exact routing excluded','edge_visits':visits,'settled_nodes':settled,'prediction_sha256':sha(out/'prediction.json'),'journal_sha256':sha(out/'net_results.jsonl'),'protocol_sha256':sha(out/'protocol.json'),'inputs_unchanged':True,'scope':'CSR authenticated witnesses and net-union occupancy; independent original XML path audit and QoR pending'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
