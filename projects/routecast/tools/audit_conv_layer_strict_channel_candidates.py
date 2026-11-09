"""Independent original XML audit of all completed FOUND avoidance witnesses."""
import json,collections,shutil
from pathlib import Path
from array import array
from prepared_csr import read
from streaming_prediction_audit import verify
from pre_route_endpoints import sha

def run():
 base=Path('experiments');parent=base/'conv_layer_strict_channel_avoidance_2026-10-06';p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text())
 assert r['queries']==75 and r['protocol_sha256']==sha(parent/'protocol.json') and r['journal_sha256']==sha(parent/'queries.jsonl')
 assert all(sha(v)==h for v,h in p['inputs_sha256'].items())
 records=[json.loads(v) for v in (parent/'queries.jsonl').read_text().splitlines()];assert len(records)==75 and len({v['connection_id'] for v in records})==75
 groups=collections.defaultdict(list)
 for v in records:groups[v['net_id']].append(v['result']['status'])
 m,f=read(base/'conv_layer_length_switch_csr_2026-10-06/csr',p['graph']['sha256']);slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 rows=[];net_nodes=collections.defaultdict(set)
 for v in records:
  if v['result']['status']!='FOUND':continue
  row={k:v[k] for k in ['connection_id','net_id','source','sink']};row.update(physical_edge_ids=v['result']['physical_edge_ids'],method='strict_channel_candidate');rows.append(row)
  used={row['source']}
  for eid in row['physical_edge_ids']:used.add(f['dest_ranks'][slots[eid]])
  assert not used&set(p['banned_channel_nodes']);net_nodes[row['net_id']].update(used)
 occupancy=collections.Counter(n for nodes in net_nodes.values() for n in nodes)
 prediction={'physical_graph_sha256':p['graph']['sha256'],'connections':rows,'node_occupancy':{str(n):v for n,v in occupancy.items()},'methods':{'strict_channel_candidate':len(rows)},'requested':len(rows),'completed':len(rows)}
 endpoints={'graph_sha256':p['graph']['sha256'],'connections':[{k:v[k] for k in ['connection_id','net_id','source','sink']} for v in rows]}
 out=base/'conv_layer_strict_channel_candidate_xml_audit_2026-10-06';out.mkdir();(out/'source').mkdir()
 names=['audit_conv_layer_strict_channel_candidates.py','streaming_prediction_audit.py','physical_prediction_audit.py','prepared_csr.py','pre_route_endpoints.py','net_union_topology.py'];sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 protocol={'parent_receipt_sha256':sha(parent/'receipt.json'),'graph':p['graph'],'source_sha256':sources,'scope':'FOUND subset original XML path audit and net-union diagnostics; incomplete nets cannot be committed; global ownership/STA pending'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 result=verify(p['graph']['path'],endpoints,prediction,topology=True);assert result['all_physical_and_union_checks_passed']
 assert all(sha(Path('tools')/n)==h for n,h in sources.items())
 receipt={'protocol_sha256':sha(out/'protocol.json'),'result':result,'whole_net_all_connections_found':[net for net,statuses in sorted(groups.items()) if all(v=='FOUND' for v in statuses)],'nets_with_failed_or_unknown_connections':[net for net,statuses in sorted(groups.items()) if any(v!='FOUND' for v in statuses)],'repair_committed':False,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'found_paths':len(rows),'all_path_checks_pass':True,'whole_nets_all_found':len(receipt['whole_net_all_connections_found']),'incomplete_nets':len(receipt['nets_with_failed_or_unknown_connections'])}),flush=True)
if __name__=='__main__':run()
