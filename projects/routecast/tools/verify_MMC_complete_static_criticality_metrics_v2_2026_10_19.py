"""Independent histogram-rank/selection/MAE metrics and all frozen cold decisions."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import json,hashlib,math,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def verify_metric(pred,truth,k,reported):
 ids=sorted(truth);assert set(pred)==set(truth);p=[pred[n] for n in ids];t=[truth[n] for n in ids];n=len(ids);histp=Counter(p);histt=Counter(t)
 def ranks(hist):
  seen=0;result={}
  for value,count in sorted(hist.items()):result[value]=2*seen+count-1;seen+=count
  return result
 xp,yt=ranks(histp),ranks(histt);mean=n-1;xx=sum(count*(xp[value]-mean)**2 for value,count in histp.items());yy=sum(count*(yt[value]-mean)**2 for value,count in histt.items());joint=Counter(zip(p,t));cross=sum(count*(xp[a]-mean)*(yt[b]-mean) for (a,b),count in joint.items());rho=cross/math.sqrt(xx*yy) if xx and yy else None
 if rho is None:assert reported['spearman'] is None
 else:assert reported['spearman'] is not None and abs(rho-reported['spearman'])<1e-12
 chosen=sorted(ids,key=lambda nid:(-pred[nid],nid))[:k];actual=sorted(ids,key=lambda nid:(-truth[nid],nid))[:k];precision=len(set(chosen)&set(actual))/k;assert precision==reported['precision_at_k']==reported['recall_at_k'];assert reported['k']==k and reported['universe_size']==n and reported['nonzero_truth']==sum(v>0 for v in t)
 if all(isinstance(v,(int,Fraction)) for v in p):
  mae=sum((abs(a-b) for a,b in zip(p,t)),Fraction())/n;assert Fraction(reported['mae'])==mae
 else:assert math.isclose(float(reported['mae']),math.fsum(float(abs(a-b)) for a,b in zip(p,t))/n,rel_tol=1e-12,abs_tol=1e-12)
 assert Fraction(reported['truth_k_boundary'])==truth[actual[-1]]
 if isinstance(pred[chosen[-1]],float):assert float(reported['prediction_k_boundary'])==pred[chosen[-1]]
 else:assert Fraction(reported['prediction_k_boundary'])==pred[chosen[-1]]
 return rho,precision

def main():
 O=R/'experiments/mmc_complete_static_criticality_cold_quality_v1_2026-10-19';result=O/'results.json';d=json.loads(result.read_text());assert not (O/'independent_metric_verification_v1.json').exists();assert d['original_full_gate_pass'] is False and d['raw_min_on_control_missing'] is True
 for p,h in d['bindings'].items():assert sha(p)==h,p
 graph=next(Path(p) for p in d['bindings'] if p.endswith('rr_graph.xml'));channels=[];capacity=Counter();stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:
    loc=e.find('loc');seg=e.find('segment');keys=[(int(loc.get('layer','0')),x,y,e.get('type'),int(seg.get('segment_id')) if seg is not None else -1) for x in range(int(loc.get('xlow')),int(loc.get('xhigh'))+1) for y in range(int(loc.get('ylow')),int(loc.get('yhigh'))+1)];cap=int(e.get('capacity'));channels.append((int(e.get('id')),cap,keys))
    for key in keys:capacity[key]+=cap
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(channels)==258720 and len(capacity)==17160;bindings={str(p):sha(p) for p in [result,graph,Path(__file__).resolve()]};source_file=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';source={int(n):Fraction(v) for n,v in json.loads(source_file.read_text())['ledger'].items()};vectors=0;decisions=[];comparison_decisions=[]
 for row in d['cases']:
  case=row['case'];candidate=R/f'experiments/mmc_complete_static_criticality_forecast_v1_2026-10-19/{case}/unique_NET_occupancy.json';ensemble=R/f'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19/{case}/expected_unique_NET_occupancy.json';predictions={'static_criticality':{int(n):Fraction(v) for n,v in json.loads(candidate.read_text()).items()},'NET_tree_ensemble':{int(n):Fraction(v) for n,v in json.loads(ensemble.read_text()).items()},'previous_native':source};files=[candidate,ensemble,source_file]
  for label,mode in [('raw_min_off','raw_min'),('native_retained_off','native_retained')]:
   p=R/f'experiments/mmc_prospective_swap_initializers_v1_2026-10-19/{case}/{mode}/initial.json';predictions[label]={int(n):Fraction(v) for n,v in json.loads(p.read_text())['ledger'].items()};files.append(p)
  target=R/f'experiments/mmc_prospective_pressure_native_v2_2026-10-19/{case}/cold/physical_audit.json';actual={int(n):Fraction(v) for n,v in json.loads(target.read_text())['node_occupancy'].items()};files.append(target);truth={};bintruth=Counter();bins={m:Counter() for m in predictions};concrete={m:{} for m in predictions}
  for n,cap,keys in channels:
   assert actual.get(n,0)<=cap;truth[n]=actual.get(n,Fraction())/cap
   for model,ledger in predictions.items():concrete[model][n]=ledger.get(n,Fraction())/cap
   for key in keys:
    bintruth[key]+=actual.get(n,0)
    for model,ledger in predictions.items():bins[model][key]+=ledger.get(n,0)
  spatial_truth={key:Fraction(bintruth[key])/cap for key,cap in capacity.items()};verified={}
  for model in predictions:
   normalized={key:Fraction(bins[model][key])/cap for key,cap in capacity.items()};verified[model]={}
   for scope,p,t,k in [('concrete',concrete[model],truth,12936),('spatial',normalized,spatial_truth,20)]:verified[model][scope]=verify_metric(p,t,k,row['metrics'][model][scope]);vectors+=1
  geometry_file=R/f'experiments/mmc_current_geometry_baseline_v1_2026-10-19/{case}.json';geometry={tuple(x['key']):x['value'] for x in json.loads(geometry_file.read_text())['bins']};verified['geometry']={'spatial':verify_metric(geometry,spatial_truth,20,row['metrics']['geometry']['spatial'])};vectors+=1;files.append(geometry_file)
  def decide(model,scopes):
   flags=[]
   for scope in scopes:
    for index in [0,1]:
     a=verified['static_criticality'][scope][index];b=verified[model][scope][index];eps=1e-12 if index==0 else 0;flags.append((a is not None and b is not None and a>=b-eps,a is not None and b is not None and a>b+eps))
   return all(a for a,b in flags) and any(b for a,b in flags)
  passed=decide('previous_native',['concrete','spatial']);assert passed==row['previous_native_necessary_gate_pass'];decisions.append(passed);extra={}
  for model,scopes in [('NET_tree_ensemble',['concrete','spatial']),('geometry',['spatial'])]:extra[model]=decide(model,scopes);assert extra[model]==row['additional_registered_comparisons'][model]['comparison_gate_pass']
  comparison_decisions.append({'case':case,'comparisons':extra})
  for p in files:assert d['bindings'][str(p)]==sha(p),str(p);bindings[str(p)]=sha(p)
  print('COMPLETE_COLD_METRICS_INDEPENDENT_PASS',case,'necessary',passed,'extra',extra,flush=True)
 assert len(decisions)==3 and vectors==33;assert d['status']==('FAIL_NECESSARY_PREVIOUS_NATIVE_CONTROL' if not all(decisions) else 'UNRESOLVED_RAW_MIN_ON_CONTROL_MISSING')
 (O/'independent_metric_verification_v1.json').write_text(json.dumps({'status':'ALL3_33_COLD_METRIC_VECTORS_MAE_AND_FROZEN_DECISIONS_INDEPENDENTLY_VERIFIED','metric_vectors':vectors,'necessary_control_gates':decisions,'additional_comparison_gates':comparison_decisions,'original_full_gate_pass':False,'raw_min_on_required_control_missing':True,'bindings':bindings,'scope':'Independent metrics and decisions on all exposed current layouts only; no native utility, full workflow or unseen-family gain.'},indent=2)+'\n');print('COMPLETE_COLD_METRICS_ALL33_PASS',flush=True)
if __name__=='__main__':main()
