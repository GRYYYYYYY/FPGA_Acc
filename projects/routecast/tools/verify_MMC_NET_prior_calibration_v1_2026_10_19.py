"""Independent grouped-score Brier/bin reconstruction and input/label matching."""
import pathlib,json,hashlib
from collections import Counter
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_NET_prior_calibration_v1_2026-10-19';rp=O/'results.json';v=json.loads(rp.read_text());assert v['status']=='ALL3_INDEPENDENT_NET_PRIOR_CHECKPOINT1_CALIBRATION_DESCRIBED'
 for p,h in v['bindings'].items():assert sha(p)==h,p
 domain=json.loads((O/'domain.json').read_text());assert len(domain)==len(set(domain))==258720 and domain==sorted(domain);rows=[]
 for row in v['cases']:
  case=row['case'];vp=O/(case+'_vectors.json');assert v['bindings'][str(vp)]==sha(vp);vectors=json.loads(vp.read_text());scores=list(map(Fraction,vectors['probabilities']));truth=vectors['actual_binary_overuse'];assert len(scores)==len(truth)==len(domain);assert all(type(y) is int and y in [0,1] for y in truth)
  source=R/'experiments/mmc_NET_prior_overflow_v1_2026-10-19'/case/'prior_statistics.json';feature=R/'experiments/mmc_prospective_pressure_targets_v2_2026-10-19'/case/'features.json';assert v['bindings'][str(source)]==sha(source) and v['bindings'][str(feature)]==sha(feature);s={int(n):Fraction(x) for n,x in json.loads(source.read_text())['probability_over_capacity'].items()};f=json.loads(feature.read_text());assert f['cutoff_iteration']==1;label={int(n):x for n,x in f['overflow_units_by_rr'].items()};assert scores==[s.get(n,Fraction(0)) for n in domain] and truth==[int(label.get(n,0)>0) for n in domain]
  joint=Counter(zip(scores,truth));n=len(domain);sse=Fraction(0);masses=[Fraction(0)]*10;positives=[0]*10;counts=[0]*10
  for (p,y),count in joint.items():
   assert 0<=p<=1;sse+=count*(p*p-2*p*y+y);bucket=sum(p>=Fraction(k,10) for k in range(1,10));counts[bucket]+=count;positives[bucket]+=count*y;masses[bucket]+=count*p
  brier=sse/n;ece=sum((abs(m-y) for m,y in zip(masses,positives)),Fraction(0))/n;assert brier==Fraction(row['brier']) and ece==Fraction(row['calibration_gap']);assert sum(truth)==row['positive_overused_channels'];assert sum(scores,Fraction(0))==Fraction(row['predicted_positive_count']);assert Fraction(row['constant_zero_brier'])==Fraction(sum(truth),n) and Fraction(row['constant_half_brier'])==Fraction(1,4)
  assert sum(count for (p,y),count in joint.items() if p==0 and y==1)==row['predict_zero_actual_overused'];assert sum(count for (p,y),count in joint.items() if p==1 and y==0)==row['predict_one_actual_not_overused']
  for i,binrow in enumerate(row['bins']):
   assert binrow['nodes']==counts[i] and binrow['positive']==positives[i] and Fraction(binrow['probability_sum'])==masses[i]
   if counts[i]:assert Fraction(binrow['mean_probability'])==masses[i]/counts[i] and Fraction(binrow['observed_frequency'])==Fraction(positives[i],counts[i])
  rows.append(dict(case=case,brier=str(brier),constant_zero_brier=row['constant_zero_brier'],brier_beats_constant_zero=brier<Fraction(row['constant_zero_brier']),calibration_gap=str(ece),predicted_positive_count=row['predicted_positive_count'],observed_positive_count=sum(truth),zero_score_actual_overused=row['predict_zero_actual_overused']));print('CALIBRATION INDEPENDENT PASS',case,'beats_zero',rows[-1]['brier_beats_constant_zero'],flush=True)
 files=[rp,pathlib.Path(__file__).resolve()];proof=dict(status='ALL3_BRIER_BINS_ECE_AND_FIRST_CHECKPOINT_LABEL_IDENTITIES_INDEPENDENTLY_VERIFIED',bindings={str(p):sha(p) for p in files},cases=rows,bins_verified=30,resource_prediction_label_pairs_verified=3*258720,new_native_jobs=0,scope='Known correlated resources and deterministic native seed, descriptive only. Input independentNET probabilities include empirical16sample multiNET marginals. Zero-score mismatches do not prove events impossible under true latent marginals; no calibration fitting or new policy effectiveness claim.')
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
if __name__=='__main__':main()
