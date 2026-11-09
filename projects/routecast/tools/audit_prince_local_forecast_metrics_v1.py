"""Independent integer doubled ranks, transposed bin aggregation, tie sensitivity."""
import json,math
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_local_metric_crosscheck_v1_2026-10-20'
def ranks2(values):
 counts=Counter(values);offset=0;lookup={}
 for value,count in sorted(counts.items()):lookup[value]=2*offset+count-1;offset+=count
 return [lookup[x] for x in values]
def check(scores,truth,k,expected):
 keys=sorted(scores);a=ranks2([scores[x] for x in keys]);b=ranks2([truth[x] for x in keys]);center=len(keys)-1;xx=sum((x-center)**2 for x in a);yy=sum((y-center)**2 for y in b);cross=sum((x-center)*(y-center) for x,y in zip(a,b));rho=None if not xx*yy else cross/math.sqrt(xx*yy)
 assert (rho is None)==(expected['spearman'] is None)
 if rho is not None:assert abs(rho-expected['spearman'])<1e-14
 # Group scores, order each equal-score class by ascending ID/key.
 groups=defaultdict(list)
 for key in keys:groups[scores[key]].append(key)
 pred=[key for score in sorted(groups,reverse=True) for key in groups[score]][:k]
 tgroups=defaultdict(list)
 for key in keys:tgroups[truth[key]].append(key)
 target=[key for score in sorted(tgroups,reverse=True) for key in tgroups[score]][:k];hit=len(set(pred)&set(target));assert hit==expected['top_k_hits'] and pred==[tuple(x) if isinstance(x,list) else x for x in expected['prediction_top_k']] and target==[tuple(x) if isinstance(x,list) else x for x in expected['truth_top_k']]
 mae=sum((abs(scores[x]-truth[x]) for x in keys),Fraction())/len(keys);assert expected['mae']==dict(numerator=mae.numerator,denominator=mae.denominator)
 boundary=scores[pred[-1]];fixed={key for key in keys if scores[key]>boundary};tie={key for key in keys if scores[key]==boundary};need=k-len(fixed);good=len(tie&set(target));base=len(fixed&set(target));low=base+max(0,need-(len(tie)-good));high=base+min(need,good);assert low<=hit<=high
 return dict(spearman=rho,hits=hit,k=k,tie_possible_hits=[low,high],boundary_tie_size=len(tie),prediction_above_capacity_count=sum(scores[x]>1 for x in keys),selected_above_capacity_count=sum(scores[x]>1 for x in pred))
def main():
 D.mkdir(exist_ok=False);quality=E/'prince_local_schedule_trial_v1_2026-10-20';vp=quality/'verification.json';v=json.loads(vp.read_text());bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)};rows=[];vectors=0
 for row in v['rows']:
  cp=Path(row['comparison']);c=json.loads(cp.read_text());sp=cp.parent/'comparison_specification.json';s=json.loads(sp.read_text());domainp=Path(s['domain_proof']);domain=json.loads(domainp.read_text());folder=domainp.parent;rp=folder/'resources.jsonl';bp=folder/'spatial_bins.json';resources=list(map(json.loads,rp.open()));bins=json.loads(bp.read_text());adj=defaultdict(list)
  for resource in resources:
   for key in resource['bins']:adj[tuple(key)].append(resource['id'])
  cap={b['id']:b['capacity'] for b in resources};bcap={tuple(b['key']):b['capacity'] for b in bins};paths=[cp,sp,domainp,rp,bp,Path(s['label_physical_audit']),Path(s['source_frame']),*[Path(a['frame']) for a in s['predictions'].values()]]
  for p in paths:bindings[str(p)]=sha(p)
  def normalize(ledger):
   ledger={int(n):count for n,count in ledger.items()};return dict(resource={n:Fraction(ledger.get(n,0),capacity) for n,capacity in cap.items()},spatial={key:Fraction(sum(ledger.get(n,0) for n in members),bcap[key]) for key,members in adj.items()})
  truth=normalize(json.loads(Path(s['label_physical_audit']).read_text())['node_occupancy']);frames={'previous_native':Path(s['source_frame']),**{name:Path(a['frame']) for name,a in s['predictions'].items()}};metrics={}
  for method,p in frames.items():
   pred=normalize(json.loads(p.read_text())['ledger']);metrics[method]={}
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:metrics[method][scope]=check(pred[scope],truth[scope],k,c['metrics'][method][scope]);vectors+=1
  gates={}
  for control in ['previous_native','raw_min_on']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=metrics['native_retained_on'][scope],metrics[control][scope];x,y=a['spearman'],b['spearman'];nonreg.extend([x is not None and y is not None and x>=y-1e-12,a['hits']>=b['hits']]);strict.extend([x is not None and y is not None and x>y+1e-12,a['hits']>b['hits']])
   gates[control]=all(nonreg) and any(strict);assert gates[control]==c['checks'][control]['pass_primary_gate']
  rows.append(dict(case=row['case'],metrics=metrics,gates=gates,resource_candidate_optimistic_tie_can_reach_previous_hits=metrics['native_retained_on']['resource']['tie_possible_hits'][1]>=metrics['previous_native']['resource']['hits']))
 assert vectors==36 and all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL36_METRIC_VECTORS_AND12_CONTROL_GATES_INDEPENDENTLY_RECONCILED',rows=rows,metric_vectors=vectors,bindings=bindings,scope='Independent doubled integer ranks, score-group TopK sets and transposed inclusive bin aggregation. Tie interval holds target TopK fixed and changes only equal predicted score tie selection; extrema not deployable unseen policy. Development diagnosis only, original gate/ties unchanged.'),indent=2)+'\n');print('INDEPENDENT_METRICS_PASS',vectors);print([(r['case'],r['resource_candidate_optimistic_tie_can_reach_previous_hits']) for r in rows])
if __name__=='__main__':main()
