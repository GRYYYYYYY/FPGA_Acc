"""Posthoc top-channel ownership and whole-net affected closure; no repair."""
import json,array,sys,collections,shutil
from pathlib import Path
from pre_route_endpoints import sha

def run():
 base=Path('experiments');parent=base/'conv_layer_length_switch_prediction_v2_2026-10-06';csr=base/'conv_layer_length_switch_csr_2026-10-06/csr'
 pp=json.loads((parent/'protocol.json').read_text());pr=json.loads((parent/'receipt.json').read_text());m=json.loads((csr/'manifest.json').read_text())
 assert sha(parent/'protocol.json')==pr['protocol_sha256'] and sha(parent/'prediction.json')==pr['prediction_sha256'] and sha(csr/'manifest.json')==pp['csr_manifest_sha256']
 data={};hashes={}
 for key in ['types','capacities','edge_ids','dest_ranks']:
  spec=m['files'][key];p=csr/spec['file'];hashes[key]=sha(p);assert hashes[key]==spec['sha256'];a=array.array(spec['type']);a.frombytes(p.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==spec['elements'];data[key]=a
 pred=json.loads((parent/'prediction.json').read_text());occupancy=pred['node_occupancy']
 ranked=sorted([(count-data['capacities'][int(raw)],int(raw)) for raw,count in occupancy.items() if data['types'][int(raw)] in (4,5) and count>data['capacities'][int(raw)]],key=lambda v:(-v[0],v[1]))
 selected={node for excess,node in ranked[:10]};edges={eid:dest for eid,dest in zip(data['edge_ids'],data['dest_ranks']) if dest in selected};owners=collections.defaultdict(set);connections=collections.defaultdict(list);nets=collections.defaultdict(list)
 for row in pred['connections']:
  nets[row['net_id']].append(row['connection_id'])
  touched={edges[eid] for eid in row['physical_edge_ids'] if eid in edges}
  for node in touched:owners[node].add(row['net_id']);connections[node].append(row['connection_id'])
 assert all(len(owners[node])==occupancy[str(node)] for node in selected)
 affected=set().union(*owners.values());closure=sorted(cid for net in affected for cid in nets[net]);assert len(closure)==len(set(closure))
 report={'prediction_sha256':pr['prediction_sha256'],'csr_manifest_sha256':pp['csr_manifest_sha256'],'payload_sha256':hashes,'selection':'10 greatest channel excess, numeric raw node ID tie order; posthoc development selection','resources':[{'node':node,'overflow':excess,'owners':sorted(owners[node]),'connections':sorted(connections[node])} for excess,node in ranked[:10]],'affected_net_ids':sorted(affected),'whole_net_connection_ids':closure,'scope':'authenticated predicted channel ownership and whole-net closure only; no native timing budget, route feasibility or accepted feedback'}
 out=base/'conv_layer_channel_conflict_frontier_v2_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'selected_resources':len(selected),'affected_nets':len(affected),'whole_net_connections':len(closure),'selected_overflow':sum(excess for excess,node in ranked[:10])}))
if __name__=='__main__':run()
