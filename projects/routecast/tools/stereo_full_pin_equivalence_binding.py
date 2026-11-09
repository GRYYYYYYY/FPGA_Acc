"""Bind all path pin witnesses to explicit architecture declarations."""
import pathlib,json,hashlib,collections,xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=BASE/'full_path_pin_witness';mapping=BASE/'endpoints_undriven_v2/mapping.json';protocol=json.loads((BASE/'endpoints_undriven_v2/protocol.json').read_text());receipt=json.loads((src/'receipt.json').read_text())
 assert sha(src/'witness.json')==receipt['witness_sha256'];assert sha(src/'source/stereo_full_path_pin_witness.py')==receipt['source_sha256']
 inputs={str(mapping):sha(mapping),str(src/'receipt.json'):sha(src/'receipt.json'),str(src/'witness.json'):sha(src/'witness.json')}
 for k in ['architecture','packed_netlist']:
  v=protocol['inputs'][k];assert sha(pathlib.Path(v['path']))==v['sha256'];inputs[v['path']]=v['sha256']
 assert inputs[str(mapping)]==receipt['inputs_sha256'][str(mapping)]
 blocks={};depth=0
 for event,e in ET.iterparse(protocol['inputs']['packed_netlist']['path'],events=('start','end')):
  if event=='start':depth+=1;continue
  if depth==2 and e.tag=='block':
   name=e.get('name');assert name not in blocks;blocks[name]=e.get('instance').split('[')[0];e.clear()
  depth-=1
 logical={};id_kind={}
 for row in json.loads(mapping.read_text())['pin_details']:
  kind=blocks[row['block']]
  if row['block_id'] in id_kind:assert id_kind[row['block_id']]==kind
  id_kind[row['block_id']]=kind
 arch=ET.parse(protocol['inputs']['architecture']['path']).getroot();declarations={};counts=collections.Counter();differences=collections.Counter()
 witness=json.loads((src/'witness.json').read_text());assert len(witness)==163220
 for row in witness:
  kind=id_kind[row['block_id']];role=row['role'];port=row['port'];key=(kind,role,port)
  if key not in declarations:
   tag='input' if role=='SINK' else 'output'
   ports=[v for pb in arch.findall('./complexblocklist/pb_type') if pb.get('name')==kind for v in pb.findall('./'+tag) if v.get('name')==port]
   physical=[(t,s,v) for t in arch.findall('./tiles/tile') for s in t.findall('./sub_tile') if any(site.get('pb_type')==kind for site in s.findall('./equivalent_sites/site')) for v in s.findall('./'+tag) if v.get('name')==port]
   assert len(ports)==len(physical)==1,key
   t,s,v=physical[0];a=ports[0].get('equivalent','none');b=v.get('equivalent','none')
   declarations[key]={'logical':a,'physical':b,'logical_pin_count':int(ports[0].get('num_pins')),'physical_pin_count':int(v.get('num_pins')),'tile':t.get('name'),'sub_tile':s.get('name')}
  decl=declarations[key];label='|'.join(key)+'|'+decl['logical']+'|'+decl['physical']
  counts[label]+=1
  if not row['packed_binding_same']:differences[label]+=1
 out=BASE/'full_pin_equivalence_binding';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 assert all(sha(pathlib.Path(p))==h for p,h in inputs.items())
 result={'inputs_sha256':inputs,'source_sha256':sha(pathlib.Path(__file__)),'declarations':{'|'.join(k):v for k,v in declarations.items()},'witness_counts':dict(counts),'different_ptc_counts':dict(differences),'scope':'explicit logical/physical architecture declarations only; instance output equivalence is not full input permutation; no actual ownership or native legality certificate'}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'different_ptc_counts':result['different_ptc_counts'],'declaration_count':len(declarations)}))
if __name__=='__main__':main()
