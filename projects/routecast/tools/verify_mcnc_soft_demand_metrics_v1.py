"""Histogram-based independent rank, top-k and MAE recomputation from authenticated vectors."""
import sys,json,math
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/mcnc_budgeted_soft_demand_v1_2026-10-07';rp=out/'comparison.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());assert [x['name'] for x in r['rows']]==['bigkey','dsip','misex3'];checked=0

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
 name=row['name'];w=out/name;v=json.loads((w/'verification.json').read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];c=json.loads((w/'sketch.json').read_text());assert row['completed']==row['required']==c['required_connections']==v['completed'];assert row['overflow_units']==v['overflow_units'];data=json.loads((w/'comparison_vectors.json').read_text());channels=data['channels'];bins=data['bins'];assert len({x['node'] for x in channels})==len(channels) and len({tuple(x['key']) for x in bins})==len(bins);methods=set(channels[0]['predictions']);assert all(set(x['predictions'])==methods for x in channels+bins);assert 'geometry' not in methods
 for method in methods:
  truth={x['node']:x['native']/x['capacity'] for x in channels};pred={x['node']:x['predictions'][method]/x['capacity'] for x in channels};audit_metric(pred,truth,row['metrics'][method]['concrete'],max(1,len(channels)//20));truth={tuple(x['key']):x['native']/x['capacity'] for x in bins};pred={tuple(x['key']):x['predictions'][method]/x['capacity'] for x in bins};audit_metric(pred,truth,row['metrics'][method]['spatial'],20)
  if method in ('shared_net','independent_connection'):
   ledger=c['ledger'] if method=='shared_net' else c['independent_connection_ledger'];assert all(x['predictions'][method]==ledger.get(str(x['node']),0) for x in channels)
 audit_metric({tuple(x['key']):x['geometry'] for x in bins},{tuple(x['key']):x['native']/x['capacity'] for x in bins},row['metrics']['geometry']['spatial'],20);assert row['metrics']['geometry']['concrete'] is None
 if not row['hard_scored']:assert row['hard_completed']<row['hard_required'] and row['metrics']['archived_hard_capacity']==dict(concrete=None,spatial=None)
 else:assert row['hard_completed']==row['hard_required'] and 'archived_hard_capacity' in methods
assert all(sha(k)==h for k,h in bindings.items());(out/'metric_verification.json').write_text(json.dumps(dict(bindings=bindings,designs=3,metric_vectors_recomputed=checked,histogram_ranks_topk_mae_and_complete_scope_pass=True,scope='Independent descriptive statistics over authenticated development vectors; not heldout-family validation, legal route or native feedback speed evidence.'),indent=2)+'\n');print('PASS soft-demand metrics',checked,flush=True)
