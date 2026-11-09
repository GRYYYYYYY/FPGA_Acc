"""Independent histogram/tie/top-k/MAE recomputation, exact complete four-case scope."""
import sys,json,math
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/resident_wire_span_hotspots_v1_2026-10-08';rp=out/'comparison.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==v for k,v in bindings.items());assert [x['name'] for x in r['rows']]==['bigkey','dsip','misex3','frisc'];checked=0
def audit_metric(pred,truth,m,k):
 global checked
 assert set(pred)==set(truth);ids=sorted(truth);k=min(k,len(ids));assert m['k']==k and m['universe_size']==len(ids);assert m['nonzero_truth']==sum(x>0 for x in truth.values())
 def rankmap(values):
  histogram=Counter(values.values());prior=0;rank={}
  for value,count in sorted(histogram.items()):rank[value]=prior+(count-1)/2;prior+=count
  return {i:rank[value] for i,value in values.items()}
 a=rankmap(pred);b=rankmap(truth);mean=(len(ids)-1)/2;cov=sum((a[i]-mean)*(b[i]-mean) for i in ids);den=math.sqrt(sum((a[i]-mean)**2 for i in ids)*sum((b[i]-mean)**2 for i in ids));corr=None if den==0 else cov/den
 if corr is None:assert m['spearman'] is None
 else:assert abs(corr-m['spearman'])<1e-12
 mae=sum(abs(pred[i]-truth[i]) for i in ids)/len(ids);assert abs(mae-m['mae'])<1e-12;ps=sorted(ids,key=lambda i:(-pred[i],i))[:k];ts=sorted(ids,key=lambda i:(-truth[i],i))[:k];hit=len(set(ps)&set(ts))/k;assert m['precision_at_k']==m['recall_at_k']==hit;assert m['truth_k_boundary']==truth[ts[-1]] and m['prediction_k_boundary']==pred[ps[-1]];checked+=1


for row in r['rows']:
 name=row['name'];data=json.loads((out/name/'comparison_vectors.json').read_text());channels=data['channels'];bins=data['bins'];assert len({x['node'] for x in channels})==len(channels);assert len({tuple(x['key']) for x in bins})==len(bins);methods={'wire_shared','wire_independent','rc_feedback','rc_initial'};assert all(set(x['predictions'])==methods and x['capacity']>0 for x in channels+bins)
 wire=R/'experiments/resident_wire_span_full_v1_2026-10-08'/name/'resident';base=R/'experiments/frisc_resident_full_workflow_v2_2026-10-07/frisc/resident' if name=='frisc' else R/'experiments/resident_full_workflow_v5_2026-10-07'/name/'resident'
 c=json.loads((wire/'sketch.json').read_text());initial=json.loads((wire/'initial.json').read_text());rc=json.loads((base/'sketch.json').read_text());assert row['completed']==row['required']==c['completed_connections']==rc['completed_connections']==initial['completed_connections'];ledgers={'wire_shared':c['ledger'],'wire_independent':c['independent_connection_ledger'],'rc_feedback':rc['ledger'],'rc_initial':initial['ledger']}
 for method in methods:
  assert all(x['predictions'][method]==ledgers[method].get(str(x['node']),0) for x in channels)
  audit_metric({x['node']:x['predictions'][method]/x['capacity'] for x in channels},{x['node']:x['native']/x['capacity'] for x in channels},row['metrics'][method]['concrete'],max(1,len(channels)//20))
  audit_metric({tuple(x['key']):x['predictions'][method]/x['capacity'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},row['metrics'][method]['spatial'],20)
 audit_metric({tuple(x['key']):x['geometry'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},row['metrics']['geometry']['spatial'],20);assert row['metrics']['geometry']['concrete'] is None
assert checked==36
(out/'metric_verification.json').write_text(json.dumps({'bindings':bindings,'designs':4,'metric_vectors_recomputed':checked,'histogram_ranks_topk_mae_and_all_complete_scope_pass':True,'heldout_family':False},indent=2)+'\n');print('PASS wire-span metrics',checked)
