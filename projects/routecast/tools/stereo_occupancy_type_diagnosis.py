"""Authenticated descriptive full-cohort occupancy decomposition by RR type."""
import pathlib,json,hashlib,array,sys,collections
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';csr=BASE/'streaming_csr_class_cache_v3/csr';evaluation=BASE/'ordinary_additive_undriven_v2_authenticated_host_evaluation'
 protocol=json.loads((parent/'protocol.json').read_text());receipt=json.loads((parent/'receipt.json').read_text());manifest=json.loads((csr/'manifest.json').read_text());er=json.loads((evaluation/'receipt.json').read_text());ep=json.loads((evaluation/'protocol.json').read_text())
 assert sha(csr/'manifest.json')==protocol['csr_manifest_sha256']
 assert sha(parent/'prediction.json')==receipt['prediction_sha256']==ep['inputs']['prediction']['sha256']
 native=pathlib.Path(ep['inputs']['native']['path']);assert sha(native)==ep['inputs']['native']['sha256']
 payload={}
 for name in ['node_ids','types','capacities']:
  spec=manifest['files'][name];p=csr/spec['file'];assert sha(p)==spec['sha256']
  a=array.array(spec['type']);a.frombytes(p.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==manifest['nodes'];payload[name]=a
 assert all(i==v for i,v in enumerate(payload['node_ids']))
 names={v:k for k,v in manifest['type_codes'].items()};reports={}
 for label,p in [('prediction',parent/'prediction.json'),('native',native)]:
  occupancy=json.loads(p.read_text())['node_occupancy'];by=collections.defaultdict(lambda:dict(occupied_nodes=0,net_node_touches=0,overused_nodes=0,overflow_units=0,maximum_occupancy=0))
  for raw,count in occupancy.items():
   i=int(raw);assert 0<=i<manifest['nodes'] and count>=0
   if not count:continue
   r=by[names[payload['types'][i]]];overflow=max(0,count-payload['capacities'][i])
   r['occupied_nodes']+=1;r['net_node_touches']+=count;r['overused_nodes']+=bool(overflow);r['overflow_units']+=overflow;r['maximum_occupancy']=max(r['maximum_occupancy'],count)
  reports[label]=dict(by)
  assert sum(v['overflow_units'] for v in by.values())==er['reports'][label+'_overflow_units']
 out=BASE/'full_occupancy_type_diagnosis';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 result={'source_sha256':sha(pathlib.Path(__file__)),'manifest_sha256':sha(csr/'manifest.json'),'prediction_sha256':receipt['prediction_sha256'],'native_sha256':sha(native),'reports':reports,'scope':'posthoc type decomposition; fixed-pin additive predictions may overuse pins; no causal proof or legal feedback'}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(reports))
if __name__=='__main__':run()
