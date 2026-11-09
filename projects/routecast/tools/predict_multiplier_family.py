"""Fixed arithmetic cohort host predictors, no native reference inputs."""
import argparse,json,time,subprocess,collections,shutil
from pathlib import Path
from array import array
from prepared_csr import read,U64
from pre_route_endpoints import sha

def run():
 parser=argparse.ArgumentParser();parser.add_argument('design');parser.add_argument('model',choices=['sparse_reset','bbox3']);args=parser.parse_args();model=args.model
 total_start=time.monotonic();base=Path('experiments');endpoint_root=base/'multiplier_family_endpoints_2026-10-06'/args.design;prepared=base/'multiplier_family_length_switch_csr_2026-10-06'/args.design;out=base/'multiplier_family_predictions_2026-10-06'/args.design/model
 prep=json.loads((prepared/'receipt.json').read_text());cp=json.loads((prepared/'protocol.json').read_text());p={'inputs':{'graph':cp['graph']}}
 assert prep['manifest_sha256']==sha(prepared/'csr/manifest.json') and prep['protocol_sha256']==sha(prepared/'protocol.json')
 auditroot=base/'multiplier_family_length_switch_csr_audit_2026-10-06'/args.design;audit=json.loads((auditroot/'receipt.json').read_text());assert audit['all_node_metadata_and_edge_costs_match_original_xml'] and audit['parent_receipt_sha256']==sha(prepared/'receipt.json') and audit['protocol_sha256']==sha(auditroot/'protocol.json')
 er=json.loads((endpoint_root/'receipt.json').read_text());ep=endpoint_root/'endpoints.json';e=json.loads(ep.read_text());expected_connections=len(e['connections']);assert er['outputs']['endpoints.json']==sha(ep) and er['protocol_sha256']==sha(endpoint_root/'protocol.json')
 frontend_protocol=json.loads((endpoint_root/'protocol.json').read_text());assert frontend_protocol['inputs']['rr_graph']==cp['graph'];assert all(sha(v['path'])==v['sha256'] for v in frontend_protocol['inputs'].values())
 accounting_root=base/'multiplier_family_endpoint_accounting_2026-10-06'/args.design;accounting=json.loads((accounting_root/'receipt.json').read_text());assert accounting['all_pin_accounting_and_endpoint_multisets_match'] and accounting['frontend_receipt_sha256']==sha(endpoint_root/'receipt.json')
 pinroot=base/'multiplier_family_pin_membership_2026-10-06'/args.design;pin=json.loads((pinroot/'pin_membership_audit.json').read_text());assert pin['mapping_sha256']==er['outputs']['mapping.json'] and pin['graph_sha256']==cp['graph']['sha256'];assert pin['all_required_direct_pin_memberships_verified'] and pin['all_requested_class_physical_pin_counts_match_capacity'];assert pin['rr_nodes']==prep['nodes']==audit['nodes'] and pin['rr_edges']==prep['edges']==audit['edges']
 binary=Path('build/routecast_csr_authenticated_bounded' if model=='bbox3' else 'build/routecast_csr_authenticated_sparse_reset')
 prior=base/'multiplier_family_native_capture_2026-10-06';frozen=json.loads((prior/'protocol.json').read_text());assert sha(binary)==frozen['frozen_predictor_sources'][str(binary)]['sha256']
 deps=[Path(__file__),Path('tools/prepared_csr.py'),Path('tools/pre_route_endpoints.py')];dependencies={str(q):sha(q) for q in deps};inputs={'graph':cp['graph'],'endpoints':{'path':str(ep.resolve()),'sha256':sha(ep)}}
 out.mkdir(parents=True);(out/'source').mkdir()
 for name in dependencies:shutil.copyfile(name,out/'source'/Path(name).name)
 shutil.copy2(binary,out/'consumer')
 protocol={'inputs':inputs,'binary_sha256':sha(binary),'source_sha256':dependencies,'csr_manifest_sha256':prep['manifest_sha256'],'conversion_receipt_sha256':sha(prepared/'receipt.json'),'physical_csr_audit_receipt_sha256':sha(auditroot/'receipt.json'),'frontend_receipt_sha256':sha(endpoint_root/'receipt.json'),'frontend_accounting_receipt_sha256':sha(accounting_root/'receipt.json'),'pin_membership_audit_sha256':sha(pinroot/'pin_membership_audit.json'),'policy_sha256':sha(endpoint_root/'protocol.json'),'pre_measurement_binary_freeze_sha256':sha(prior/'protocol.json'),'model':model,'bbox_margin_grid_units':3 if model=='bbox3' else None,'order':'ascending NET/CID/distinct sink','scope':'frozen arithmetic cohort predictor; no native label input, parameter tuning or unseen-family claim'}
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
     rows.append({**row,'physical_edge_ids':path,'method':model if path is not None else 'failed'})
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
