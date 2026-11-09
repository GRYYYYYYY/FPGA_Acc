"""Complete direct SOURCE->OPIN catalog for mapped classes; no path feasibility."""
import pathlib,json,array,sys,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 csr=BASE/'streaming_csr_class_cache_v3/csr';mapping=BASE/'endpoints_undriven_v2/mapping.json';parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';m=json.loads((csr/'manifest.json').read_text());pp=json.loads((parent/'protocol.json').read_text())
 assert sha(csr/'manifest.json')==pp['csr_manifest_sha256'];assert sha(mapping)=='1d5eade4989216c49450de200e39eb65b41f80de1537cbd580e5ec47d2b3bbb2'
 inputs={str(mapping):sha(mapping),str(csr/'manifest.json'):sha(csr/'manifest.json')};data={}
 for key in ['node_ids','types','capacities','ptc','row_offsets','dest_ranks','edge_ids','switch_ids','costs']:
  spec=m['files'][key];f=csr/spec['file'];h=sha(f);assert h==spec['sha256'];inputs[str(f)]=h;a=array.array(spec['type']);a.frombytes(f.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==spec['elements'];data[key]=a
 assert all(i==v for i,v in enumerate(data['node_ids']))
 classes=collections.defaultdict(list)
 for r in json.loads(mapping.read_text())['pin_details']:
  if r['role']=='SOURCE':classes[r['rr_node']].append(r)
 catalog=[];owner={};total=0;arcs=0
 for cls,bindings in sorted(classes.items()):
  assert data['types'][cls]==m['type_codes']['SOURCE'];pins=collections.defaultdict(list)
  for arc in range(data['row_offsets'][cls],data['row_offsets'][cls+1]):
   dest=data['dest_ranks'][arc];assert data['types'][dest]==m['type_codes']['OPIN'];assert data['capacities'][dest]==1
   if dest in owner:assert owner[dest]==cls
   owner[dest]=cls;pins[dest].append({'edge_id':data['edge_ids'][arc],'switch_id':data['switch_ids'][arc],'cost':data['costs'][arc],'disabled':data['costs'][arc]==m['disabled_cost_sentinel']});arcs+=1
  assert len(pins)==data['capacities'][cls]
  ptcs=[data['ptc'][node] for node in pins];assert len(set(ptcs))==len(ptcs)
  assert all(r['physical_pin_ptc'] in ptcs for r in bindings)
  catalog.append({'source_class':cls,'capacity':data['capacities'][cls],'mapped_net_ids':sorted(r['net_id'] for r in bindings),'pins':[{'node':node,'ptc':data['ptc'][node],'arcs':edges} for node,edges in sorted(pins.items())]});total+=len(pins)
 assert len(classes)==9678
 assert all(sha(pathlib.Path(p))==h for p,h in inputs.items())
 out=BASE/'source_opin_catalog';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes());(out/'catalog.json').write_text(json.dumps(catalog)+'\n')
 receipt={'inputs_sha256':inputs,'source_sha256':sha(pathlib.Path(__file__)),'catalog_sha256':sha(out/'catalog.json'),'source_classes':len(classes),'physical_opins':total,'direct_arcs':arcs,'scope':'authenticated CSR direct physical members including excluded classes; class count/capacity and packed membership verified; no target reachability, timing feasibility, or free ownership proof'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['inputs_sha256','source_sha256']}))
if __name__=='__main__':main()
