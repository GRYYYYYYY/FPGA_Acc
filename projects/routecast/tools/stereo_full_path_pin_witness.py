"""Full predicted physical pin witness versus packed pin binding, diagnostic only."""
import pathlib,json,array,sys,hashlib,bisect,collections,time
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1048576),b''):h.update(c)
 return h.hexdigest()
def main():
 start=time.monotonic();parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';csr=BASE/'streaming_csr_class_cache_v3/csr';mapping=BASE/'endpoints_undriven_v2/mapping.json';out=BASE/'full_path_pin_witness';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());m=json.loads((csr/'manifest.json').read_text())
 assert sha(parent/'prediction.json')==r['prediction_sha256'];assert sha(csr/'manifest.json')==p['csr_manifest_sha256'];assert sha(mapping)=='1d5eade4989216c49450de200e39eb65b41f80de1537cbd580e5ec47d2b3bbb2'
 inputs={str(v):sha(v) for v in [parent/'protocol.json',parent/'receipt.json',parent/'prediction.json',csr/'manifest.json',mapping]}
 pred=json.loads((parent/'prediction.json').read_text())['connections'];assert len(pred)==81610
 wanted={e for v in pred for e in (v['physical_edge_ids'][0],v['physical_edge_ids'][-1])}
 data={}
 for k in ['node_ids','edge_ids','dest_ranks','row_offsets','types','ptc']:
  spec=m['files'][k];f=csr/spec['file'];assert sha(f)==spec['sha256'];inputs[str(f)]=spec['sha256'];a=array.array(spec['type']);a.frombytes(f.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==spec['elements'];data[k]=a
 endpoints={}
 for arc,eid in enumerate(data['edge_ids']):
  if eid in wanted:
   source=bisect.bisect_right(data['row_offsets'],arc)-1
   endpoints[eid]=(data['node_ids'][source],data['node_ids'][data['dest_ranks'][arc]])
 assert set(endpoints)==wanted
 rows=json.loads(mapping.read_text())['pin_details'];lookup={}
 for v in rows:
  key=(v['net_id'],v['rr_node'],v['role'])
  assert key not in lookup;lookup[key]=v
 counts=collections.Counter();ports=collections.defaultdict(collections.Counter);witness=[]
 for q in pred:
  for role,node,edge in [('SOURCE',q['source'],q['physical_edge_ids'][0]),('SINK',q['sink'],q['physical_edge_ids'][-1])]:
   a,b=endpoints[edge];actual=b if role=='SOURCE' else a
   assert (a if role=='SOURCE' else b)==node
   assert data['types'][actual]==m['type_codes']['OPIN' if role=='SOURCE' else 'IPIN']
   binding=lookup[(q['net_id'],node,role)];same=data['ptc'][actual]==binding['physical_pin_ptc']
   counts[role+'_total']+=1;counts[role+('_same' if same else '_different')]+=1
   ports[role+':'+binding['port']]['same' if same else 'different']+=1
   witness.append({'connection_id':q['connection_id'],'net_id':q['net_id'],'role':role,'class_node':node,'actual_pin_node':actual,'actual_ptc':data['ptc'][actual],'packed_ptc':binding['physical_pin_ptc'],'packed_binding_same':same,'block_id':binding['block_id'],'port':binding['port']})
 assert all(sha(pathlib.Path(k))==v for k,v in inputs.items())
 (out/'witness.json').write_text(json.dumps(witness)+'\n')
 result={'inputs_sha256':inputs,'source_sha256':sha(pathlib.Path(__file__)),'witness_sha256':sha(out/'witness.json'),'counts':dict(counts),'by_role_port':{k:dict(v) for k,v in ports.items()},'wall_s':time.monotonic()-start,'scope':'physical path pin vs packed binding; different ptc does not establish illegality, equivalence, or available ownership; per-connection SOURCE counts duplicate fanout'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'counts':result['counts'],'by_role_port':result['by_role_port'],'wall_s':result['wall_s']}))
if __name__=='__main__':main()
