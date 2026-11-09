"""Known-data descriptive calibration vs admitted zero-policy checkpoint1."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def serial(x):
 if isinstance(x,Fraction):return str(x)
 if isinstance(x,dict):return {str(k):serial(v) for k,v in x.items()}
 if isinstance(x,(tuple,list)):return [serial(v) for v in x]
 return x
def write(p,j):
 with p.open('x') as f:json.dump(serial(j),f,separators=(',',':'));f.write('\n')
def main():
 M=R/'experiments/mmc_NET_prior_overflow_v1_2026-10-19';vp=M/'verification.json';v=json.loads(vp.read_text());ip=M/'independent_verification_v1.json';ind=json.loads(ip.read_text());assert ind['status']=='ALL3_PRIOR_STATISTICS_INDEPENDENT_PRODUCT_ODDS_RECONSTRUCTION_PASS' and ind['bindings'][str(vp)]==sha(vp);labels=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19';lp=labels/'verification.json';lv=json.loads(lp.read_text());assert lv['status']=='all3_admitted_traces_split_at_iteration1';graph=next(pathlib.Path(p) for p in v['bindings'] if p.endswith('rr_graph.xml'));assert sha(graph)==v['bindings'][str(graph)];O=R/'experiments/mmc_NET_prior_calibration_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [vp,ip,lp,graph,pathlib.Path(__file__).resolve()]};write(O/'protocol.json',dict(bindings=bindings,target='Actual binary overflow at complete iteration1_end_after_local_opins of admitted zero/unseeded native run',domain='All258720positiveCHAN capacity1 nodes, zeros retained',metrics=['exact mean Brier score','10equal-width probability bins including empty bins','exact weighted absolute calibration gap','hard zero-positive and one-negative contradictions'],controls=['constant0','constant1/2'],scope='Exposed known-family deterministic-seed data diagnostic, no probability fitting, threshold/K selection, new native jobs or generalization/confidence claims. PerRR dependence retained; no iid confidence intervals.'))
 domain=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['CHANX','CHANY'] and int(e.get('capacity'))>0:assert int(e.get('capacity'))==1;domain.append(int(e.get('id')))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 domain.sort();assert len(domain)==258720;write(O/'domain.json',domain);bindings[str(O/'domain.json')]=sha(O/'domain.json');rows=[]
 for case in ['episode_01','episode_02','episode_03']:
  pp=M/case/'prior_statistics.json';assert v['bindings'][str(pp)]==sha(pp);pred={int(n):Fraction(x) for n,x in json.loads(pp.read_text())['probability_over_capacity'].items()};fp=labels/case/'features.json';assert lv['bindings'][str(fp)]==sha(fp);feature=json.loads(fp.read_text());assert feature['schema']=='MMC_FIRST_CHECKPOINT_OVERFLOW_FEATURES_V1' and feature['cutoff_iteration']==1 and feature['graph_sha256']==sha(graph) and feature['phase']=='iteration_end_after_local_opins';truth={int(n):int(x)>0 for n,x in feature['overflow_units_by_rr'].items()};p=[pred.get(n,Fraction(0)) for n in domain];y=[int(truth.get(n,False)) for n in domain];assert all(0<=x<=1 for x in p);n=len(domain);positive=sum(y);brier=sum(((x-t)**2 for x,t in zip(p,y)),Fraction(0))/n;bins=[dict(index=i,nodes=0,positive=0,probability_sum=Fraction(0)) for i in range(10)]
  for x,t in zip(p,y):
   bucket=min(9,(10*x.numerator)//x.denominator);bins[bucket]['nodes']+=1;bins[bucket]['positive']+=t;bins[bucket]['probability_sum']+=x
  ece=sum((abs(x['probability_sum']-x['positive']) for x in bins),Fraction(0))/n
  for x in bins:
   x['mean_probability']=x['probability_sum']/x['nodes'] if x['nodes'] else None;x['observed_frequency']=Fraction(x['positive'],x['nodes']) if x['nodes'] else None
  row=dict(case=case,domain=n,positive_overused_channels=positive,predicted_positive_count=sum(p,Fraction(0)),brier=brier,constant_zero_brier=Fraction(positive,n),constant_half_brier=Fraction(1,4),calibration_gap=ece,predict_zero_actual_overused=sum(x==0 and t==1 for x,t in zip(p,y)),predict_one_actual_not_overused=sum(x==1 and t==0 for x,t in zip(p,y)),bins=bins);rows.append(row);vector=O/(case+'_vectors.json');write(vector,dict(probabilities=p,actual_binary_overuse=y));bindings.update({str(q):sha(q) for q in [pp,fp,vector]});print(case,'Brier',float(brier),'zero',positive/n,'ECE',float(ece),'hard_zero_misses',row['predict_zero_actual_overused'],flush=True)
 write(O/'results.json',dict(status='ALL3_INDEPENDENT_NET_PRIOR_CHECKPOINT1_CALIBRATION_DESCRIBED',bindings=bindings,cases=rows,independent_metric_audit_pending=True,calibrated_native_probability_claim=False,new_native_jobs=0,native_utility_and_final_occupancy_failures_unchanged=True,scope='Descriptive comparison of independentNET prior with deterministic native iteration1 on exposed data. Brier/ECE are descriptive over correlated resources; no fitted calibration, validation-family claim or cause-of-failure proof.'))
if __name__=='__main__':main()
