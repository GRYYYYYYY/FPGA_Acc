"""Complete conv_layer existing length-switch host baseline after full CSR audit."""
import json,time,subprocess,collections,shutil
from pathlib import Path
from array import array
from prepared_csr import read,U64
from pre_route_endpoints import sha

def run():
 expected_connections=21140;total_start=time.monotonic();base=Path('experiments');prepared=base/'conv_layer_length_switch_csr_2026-10-06';endpoint_root=base/'conv_layer_global_frontend_v2_2026-10-06';out=base/'conv_layer_length_switch_prediction_v2_2026-10-06'
 if out.exists():raise ValueError('fresh output required')
 prep=json.loads((prepared/'receipt.json').read_text());cp=json.loads((prepared/'protocol.json').read_text());p={'inputs':{'graph':cp['graph']}}
 assert prep['manifest_sha256']==sha(prepared/'csr/manifest.json') and prep['protocol_sha256']==sha(prepared/'protocol.json')
 auditroot=base/'conv_layer_length_switch_csr_audit_2026-10-06';audit=json.loads((auditroot/'receipt.json').read_text());assert audit['all_node_metadata_and_edge_costs_match_original_xml'];assert audit['parent_receipt_sha256']==sha(prepared/'receipt.json') and audit['protocol_sha256']==sha(auditroot/'protocol.json')
 accounting=json.loads((base/'conv_layer_frontend_accounting_v2_2026-10-06/receipt.json').read_text());assert accounting['all_pin_accounting_and_endpoint_multisets_match'] and accounting['retained_connections']==expected_connections
 ep=endpoint_root/'endpoints.json';er=json.loads((endpoint_root/'receipt.json').read_text());e=json.loads(ep.read_text());assert er['outputs']['endpoints.json']==sha(ep) and len(e['connections'])==expected_connections
 assert er['protocol_sha256']==sha(endpoint_root/'protocol.json')
 frontend_protocol=json.loads((endpoint_root/'protocol.json').read_text())
 assert all(sha(v['path'])==v['sha256'] for v in frontend_protocol['inputs'].values())
 assert frontend_protocol['inputs']['rr_graph']==cp['graph']
 assert all(sha(endpoint_root/'source'/name)==digest for name,digest in frontend_protocol['source_sha256'].items())
 assert all(sha(endpoint_root/name)==digest for name,digest in er['outputs'].items())
 original_root=base/'conv_layer_frozen_frontend_2026-10-06';original_receipt=json.loads((original_root/'receipt.json').read_text())
 assert sha(original_root/'receipt.json')==frontend_protocol['parent_frontend_receipt_sha256']
 assert original_receipt['protocol_sha256']==sha(original_root/'protocol.json')
 assert all(sha(original_root/name)==digest for name,digest in original_receipt['outputs'].items())
 assert json.loads((original_root/'mapping.json').read_text())['pin_details']==json.loads((endpoint_root/'mapping.json').read_text())['pin_details']
 assert accounting['frontend_receipt_sha256']==sha(endpoint_root/'receipt.json')
 assert len({v['net_id'] for v in e['connections']})==12867
 pinroot=base/'conv_layer_pin_membership_2026-10-06';pin=json.loads((pinroot/'pin_membership_audit.json').read_text())
 assert pin['mapping_sha256']==original_receipt['outputs']['mapping.json'] and pin['graph_sha256']==cp['graph']['sha256']
 assert pin['all_required_direct_pin_memberships_verified'] and pin['all_requested_class_physical_pin_counts_match_capacity']
 assert pin['rr_nodes']==prep['nodes']==audit['nodes']==873536 and pin['rr_edges']==prep['edges']==audit['edges']==12806542
 inputs={'graph':cp['graph'],'endpoints':{'path':str(ep.resolve()),'sha256':sha(ep)}};assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 binary=Path('build/routecast_csr_authenticated');dependencies={str(q):sha(q) for q in (Path(__file__),Path('tools/prepared_csr.py'),Path('tools/pre_route_endpoints.py'),Path('tools/csr_consumer/authenticated_main.cpp'),Path('tools/csr_consumer/authenticated_host_search.hpp'))};out.mkdir();(out/'source').mkdir()
 for name in dependencies:shutil.copyfile(name,out/'source'/Path(name).name)
 shutil.copy2(binary,out/'consumer');shutil.copyfile(__file__,out/'driver.py')
 protocol={'inputs':inputs,'binary_sha256':sha(binary),'source_sha256':dependencies,'csr_manifest_sha256':prep['manifest_sha256'],'conversion_receipt_sha256':sha(prepared/'receipt.json'),'physical_csr_audit_receipt_sha256':sha(auditroot/'receipt.json'),'frontend_receipt_sha256':sha(endpoint_root/'receipt.json'),'frontend_accounting_receipt_sha256':sha(base/'conv_layer_frontend_accounting_v2_2026-10-06/receipt.json'),'pin_membership_audit_sha256':sha(pinroot/'pin_membership_audit.json'),'policy_sha256':sha(endpoint_root/'protocol.json'),'revision_provenance':frontend_protocol['revision_provenance'],'original_pin_membership_preserved':True,'method':'existing rr_length_switch, no tuning','order':'ascending net, CID, distinct sink ID','scope':'complete conv_layer host baseline; no native labels or unseen-family/QoR/net-benefit claim'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');assert sha(out/'consumer')==protocol['binary_sha256']
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
 assert sha(out/'consumer')==protocol['binary_sha256'] and sha(endpoint_root/'protocol.json')==protocol['policy_sha256']
 prediction={'physical_graph_sha256':p['inputs']['graph']['sha256'],'connections':rows,'node_occupancy':{str(n):v for n,v in occupancy.items()},'requested':len(rows),'completed':len(rows)-failed,'methods':dict(collections.Counter(r['method'] for r in rows))}
 (out/'prediction.json').write_text(json.dumps(prediction)+'\n')
 assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 receipt={'connections':len(rows),'nets':len(groups),'failed':failed,'csr_verify_s':verify,'authenticate_and_output_setup_s':setup_s,'transport_index_and_group_s':index_s,'search_ledger_s':query_s,'postprocess_and_write_s':time.monotonic()-query_end,'full_prediction_wall_s':time.monotonic()-total_start,'cold_conversion_wall_s':prep['wall_s'],'timing_scope':'full prediction driver includes authentication/indexing/consumer loading/search/ledger/output; conversion separate; upstream endpoints/native cost export/independent offline audits/feedback/exact routing excluded','edge_visits':visits,'settled_nodes':settled,'prediction_sha256':sha(out/'prediction.json'),'journal_sha256':sha(out/'net_results.jsonl'),'protocol_sha256':sha(out/'protocol.json'),'inputs_unchanged':True,'scope':'CSR authenticated witnesses and net-union occupancy; independent original XML path audit and QoR pending'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
