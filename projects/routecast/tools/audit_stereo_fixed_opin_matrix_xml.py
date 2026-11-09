"""Original-XML individual physical audit of complete OPIN candidate matrix."""
import pathlib,json,hashlib,time,array,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 matrix=BASE/'fixed_opin_candidate_matrix';completion=BASE/'fixed_opin_candidate_matrix_completion/receipt.json';parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';witness=BASE/'full_path_pin_witness/witness.json';affected=BASE/'additional_high_fanout_physical_audit/affected_conflict_connections.json'
 c=json.loads(completion.read_text());assert c['queries']==200 and c['complete_expected_query_order'];assert c['parent_receipt_sha256']==sha(matrix/'receipt.json')
 r=json.loads((matrix/'receipt.json').read_text());assert r['results_sha256']==sha(matrix/'results.json');rows=[v for v in json.loads((matrix/'results.json').read_text()) if v['status']=='FOUND']
 requests={v['connection_id']:v for v in json.loads(affected.read_text())['affected_connections']};pins={(v['connection_id'],v['role']):v['actual_pin_node'] for v in json.loads(witness.read_text())}
 graph=json.loads((parent/'protocol.json').read_text())['inputs']['graph'];assert sha(graph['path'])==graph['sha256']
 inputs={str(p):sha(p) for p in [completion,matrix/'receipt.json',matrix/'results.json',affected,witness]};out=BASE/'fixed_opin_matrix_xml_audit';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes());source=sha(pathlib.Path(__file__))
 protocol={'inputs_sha256':inputs,'graph':graph,'source_sha256':source,'scope':'individual candidate physical paths only; alternatives not simultaneous; no joint occupancy, tree timing, ownership or accepted repair'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 wanted={eid for v in rows for eid in v['physical_edge_ids']};records={};types=array.array('B');caps=array.array('Q');codes={'SOURCE':0,'SINK':1,'OPIN':2,'IPIN':3,'CHANX':4,'CHANY':5};switches=set();count=0;stack=[];start=time.monotonic()
 for event,e in ET.iterparse(graph['path'],events=('start','end')):
  if event=='start':stack.append(e);continue
  parenttag=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parenttag=='rr_nodes':
   assert int(e.get('id'))==len(types);types.append(codes[e.get('type')]);caps.append(int(e.get('capacity')))
  elif e.tag=='switch' and parenttag=='switches':switches.add(int(e.get('id')))
  elif e.tag=='edge' and parenttag=='rr_edges':
   if count in wanted:records[count]=(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id')))
   count+=1
  if parenttag in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(e);e.clear()
  stack.pop()
 assert count==39165143 and len(types)==3593250 and set(records)==wanted
 for v in rows:
  q=requests[v['connection_id']];nodes=[q['source']]
  for eid in v['physical_edge_ids']:
   a,b,sid=records[eid];assert a==nodes[-1] and sid in switches;nodes.append(b)
  assert nodes[-1]==q['sink'] and len(nodes)==len(set(nodes));assert all(caps[n]>0 for n in nodes)
  assert len(nodes)>=4 and [types[nodes[i]] for i in [0,1,-2,-1]]==[0,2,3,1]
  assert all(types[n] in (4,5) for n in nodes[2:-2]);assert nodes[1]==v['opin'] and nodes[-2]==pins[v['connection_id'],'SINK']
 assert sha(graph['path'])==graph['sha256'];assert all(sha(p)==h for p,h in inputs.items());assert sha(pathlib.Path(__file__))==source
 result={'checked_found_paths':len(rows),'all_individual_original_xml_checks_pass':True,'unique_selected_edges':len(wanted),'original_xml_edges':count,'protocol_sha256':sha(out/'protocol.json'),'wall_s':time.monotonic()-start,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
