"""Fixed equal occupancy mixture on exposed layouts, not physical route commits."""
import pathlib,json,hashlib,time,sys,math
from collections import Counter
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from prediction_metrics import compare
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def independent(p,t,k):
 ids=sorted(t);n=len(ids)
 def rank(v):
  counts=Counter(v.values());offset=0;result={}
  for x,c in sorted(counts.items()):result[x]=offset+(c-1)/2;offset+=c
  return result
 a,b=rank(p),rank(t);mean=(n-1)/2;cross=sum((a[p[i]]-mean)*(b[t[i]]-mean) for i in ids);den=math.sqrt(sum((a[p[i]]-mean)**2 for i in ids)*sum((b[t[i]]-mean)**2 for i in ids));rho=cross/den if den else None
 top=lambda v:set(sorted(ids,key=lambda i:(-v[i],i))[:k])
 return rho,len(top(p)&top(t))/k

def main():
 out=R/'experiments/mmc_equal_prior_mixture_v1_2026-10-18';protocol=out/'protocol.json';spec=json.loads(protocol.read_text());assert spec['candidate']=='half_previous_native_plus_half_raw_min_on';assert all(sha(k)==h for k,h in spec['bindings'].items());tick=time.perf_counter();results=[]
 for case in spec['cases']:
  folder=R/f'experiments/mmc_atomic_pair_quality_v1_2026-10-18/{case}';audit=json.loads((folder/'verification.json').read_text());assert audit['status']=='pass';vpath=folder/'vectors.json';assert audit['bindings'][str(vpath)]==sha(vpath);data=json.loads(vpath.read_text());predictions={}
  for domain,rows in [('concrete',data['channels']),('spatial',data['bins'])]:
   key='node' if domain=='concrete' else 'key';predictions[domain]=[dict(identity=x[key],numerator=x['predictions']['previous_native']+x['predictions']['raw_min_on'],denominator=2*x['capacity']) for x in rows]
  prediction_path=out/(case+'_predictions.json');prediction_path.write_text(json.dumps(predictions,separators=(',',':'))+'\n');metrics={};checks=[]
  for domain,rows in [('concrete',data['channels']),('spatial',data['bins'])]:
   key='node' if domain=='concrete' else 'key';identity=lambda x:x[key] if key=='node' else tuple(x[key]);truth={identity(x):x['labels']['cold']/x['capacity'] for x in rows};k=len(rows)//20 if domain=='concrete' else 20
   candidate={identity(x):(x['predictions']['previous_native']+x['predictions']['raw_min_on'])/(2*x['capacity']) for x in rows};methods={'equal_mixture':candidate,**{m:{identity(x):x['predictions'][m]/x['capacity'] for x in rows} for m in spec['controls']}};metrics[domain]={}
   for m,p in methods.items():
    metric=compare(p,truth,k);rho,precision=independent(p,truth,k);assert abs(metric['spearman']-rho)<1e-12 and metric['precision_at_k']==precision;metrics[domain][m]=metric
   for m in spec['controls']:
    for measure in ['spearman','precision_at_k']:
     a,b=metrics[domain]['equal_mixture'][measure],metrics[domain][m][measure];eps=1e-12 if measure=='spearman' else 0;checks.append(dict(domain=domain,control=m,metric=measure,nonregression=a>=b-eps,strict=a>b+eps))
  gates={m:all(x['nonregression'] for x in checks if x['control']==m) and any(x['strict'] for x in checks if x['control']==m) for m in spec['controls']};results.append(dict(case=case,metrics=metrics,checks=checks,control_gates=gates,primary_gate_pass=all(gates.values()),prediction_sha256=sha(prediction_path)))
 assert all(sha(k)==h for k,h in spec['bindings'].items());result=dict(status='fixed_equal_mixture_evaluated_all3_development_cases',protocol_sha256=sha(protocol),cases=results,primary_gate_pass=all(x['primary_gate_pass'] for x in results),independent_histogram_and_topK_checks=24,seconds=time.perf_counter()-tick,accepted_gain=False,physical_path_candidate=False,heldout_family=False,scope='Fractional expected demand only. Input projections use old native and raw_min_on; target labels used for evaluation only after prediction serialization. Already exposed development data. No weight selection, no path legality/budget or native policy utility claim.')
 (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print([(x['case'],x['control_gates']) for x in results],flush=True)
if __name__=='__main__':main()
