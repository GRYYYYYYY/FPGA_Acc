"""Posthoc descriptive diagnosis; never changes predictor costs or acceptance gates."""
import hashlib,json,pathlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
SRC=BASE/'ordinary_additive_undriven_v2_authenticated_host_evaluation'
OUT=BASE/'frozen_spatial_hotspot_diagnosis'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 OUT.mkdir(exist_ok=True)
 inputs={n:sha(SRC/n) for n in ('completion.json','protocol.json','receipt.json','spatial_maps.json')}
 receipt=json.loads((SRC/'receipt.json').read_text())
 completion=json.loads((SRC/'completion.json').read_text())
 assert inputs['receipt.json']==completion['receipt_sha256']
 assert inputs['protocol.json']==receipt['protocol_sha256']
 assert inputs['spatial_maps.json']==receipt['spatial_maps_sha256']
 assert receipt['inputs_unchanged'] and receipt['exact_full_cohort_match']
 maps=json.loads((SRC/'spatial_maps.json').read_text())
 pred,native=maps['prediction'],maps['native']
 universe=set(pred)|set(native)
 orders={name:sorted(universe,key=lambda k:(-values.get(k,0),k)) for name,values in [('prediction',pred),('native',native)]}
 ranks={name:{k:i+1 for i,k in enumerate(order)} for name,order in orders.items()}
 assert len(universe)==receipt['reports']['spatial']['universe_size']
 assert not set(orders['prediction'][:20])&set(orders['native'][:20])
 report={'scope':'posthoc frozen-map descriptive diagnosis; no tuning, held-out claim, causal attribution, or accepted repair','inputs_sha256':inputs,'source_sha256':sha(pathlib.Path(__file__)),'universe_size':len(universe),'top20':{},'overlap_by_k':{}}
 for name,values in [('prediction',pred),('native',native)]:
  order=orders[name]; other='native' if name=='prediction' else 'prediction'
  boundary=values.get(order[19],0)
  report['top20'][name]={'boundary':boundary,'strictly_above_boundary':sum(values.get(k,0)>boundary for k in universe),'equal_to_boundary':sum(values.get(k,0)==boundary for k in universe),'types':dict(collections.Counter(k.split(',')[2] for k in order[:20])),'rows':[{'id':k,'prediction':pred.get(k,0),'native':native.get(k,0),'other_rank':ranks[other][k]} for k in order[:20]]}
 for k in [20,50,100,200,500,1000,2000]:
  hits=len(set(orders['prediction'][:k])&set(orders['native'][:k]))
  report['overlap_by_k'][str(k)]={'hits':hits,'precision':hits/k}
 assert all(sha(SRC/n)==v for n,v in inputs.items())
 (OUT/'source').mkdir(exist_ok=True)
 (OUT/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 (OUT/'completion.json').write_text(json.dumps({'inputs_unchanged':True,'source_sha256':report['source_sha256'],'report_sha256':sha(OUT/'report.json'),'scope':report['scope']},indent=2)+'\n')
 print(json.dumps({'overlap_by_k':report['overlap_by_k'],'top20':{k:{f:v for f,v in r.items() if f!='rows'} for k,r in report['top20'].items()}}))
if __name__=='__main__':main()
