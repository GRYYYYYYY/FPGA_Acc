"""Frozen descriptive concentration analysis; no candidate selection or tuning."""
import pathlib,json,array,hashlib,sys,collections,math
ROOT=pathlib.Path(__file__).resolve().parents[1];BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parent=BASE/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';csr=BASE/'streaming_csr_class_cache_v3/csr';prior=BASE/'full_occupancy_type_diagnosis'
 pp=json.loads((parent/'protocol.json').read_text());pr=json.loads((parent/'receipt.json').read_text());m=json.loads((csr/'manifest.json').read_text());d=json.loads((prior/'report.json').read_text());c=json.loads((prior/'completion.json').read_text())
 assert sha(prior/'report.json')==c['report_sha256'] and c['all_receipt_bindings_and_aggregate_checks_pass']
 assert sha(csr/'manifest.json')==pp['csr_manifest_sha256']==d['manifest_sha256']
 assert sha(parent/'prediction.json')==pr['prediction_sha256']==d['prediction_sha256']
 payload={};inputs={'manifest':sha(csr/'manifest.json'),'prediction':sha(parent/'prediction.json'),'prior_report':sha(prior/'report.json'),'prior_completion':sha(prior/'completion.json')}
 for key in ['node_ids','types','capacities','xlow','ylow']:
  spec=m['files'][key];p=csr/spec['file'];h=sha(p);assert h==spec['sha256'];inputs[key]=h
  a=array.array(spec['type']);a.frombytes(p.read_bytes())
  if sys.byteorder!='little':a.byteswap()
  assert len(a)==m['nodes'];payload[key]=a
 assert all(i==v for i,v in enumerate(payload['node_ids']))
 occupancy=json.loads((parent/'prediction.json').read_text())['node_occupancy'];report={}
 for name in ['OPIN','IPIN']:
  rows=[];tiles=collections.Counter();hist=collections.Counter()
  for raw,count in occupancy.items():
   i=int(raw)
   if payload['types'][i]!=m['type_codes'][name]:continue
   excess=max(0,count-payload['capacities'][i])
   if excess:
    rows.append((excess,i,count));tiles[(payload['xlow'][i],payload['ylow'][i])]+=excess;hist[count]+=1
  rows.sort(key=lambda v:(-v[0],v[1]));total=sum(v[0] for v in rows)
  assert total==d['reports']['prediction'][name]['overflow_units']
  assert len(rows)==d['reports']['prediction'][name]['overused_nodes']
  running=0;thresholds={}
  for index,row in enumerate(rows,1):
   running+=row[0]
   for pct in [50,90,95]:
    if str(pct) not in thresholds and running*100>=total*pct:thresholds[str(pct)]={'resources':index,'fraction_of_overused_resources':index/len(rows)}
  report[name]={'overused_resources':len(rows),'overflow_units':total,'tiles_with_overflow':len(tiles),'occupancy_histogram':dict(sorted(hist.items())),'cumulative_overflow_thresholds':thresholds,'top_resource_overflow':{str(k):sum(v[0] for v in rows[:k]) for k in [10,100,1000]},'top_tiles':[{'x':xy[0],'y':xy[1],'overflow_units':value} for xy,value in sorted(tiles.items(),key=lambda v:(-v[1],v[0]))[:10]]}
 out=BASE/'pin_overflow_concentration';out.mkdir(exist_ok=False);(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 result={'inputs_sha256':inputs,'source_sha256':sha(pathlib.Path(__file__)),'reports':report,'scope':'posthoc fixed-input concentration diagnosis; not class ownership proof, causal attribution, or repair acceptance'}
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:{f:v for f,v in r.items() if f not in ['occupancy_histogram','top_tiles']} for k,r in report.items()}))
if __name__=='__main__':main()
