"""Independent raw-histogram residual fits and percall loss audit."""
import json,struct,math
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_query_joint_prediction_v1_2026-10-20';S=E/'prince_future_query_joint_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def num(w):return round(struct.unpack('<f',int(w).to_bytes(4,'little'))[0])
def main():
 x=load(D/'evaluation_v1.json')
 for p,h in x['bindings'].items():assert sha(p)==h
 manifest=load(S/'dataset_manifest.json');data={};features={}
 for row in manifest['rows']:
  if row['status']!='FUTURE_QUERY_LABELS_EXTRACTED':continue
  for p in [row['target_file'],row['ready_feature_file']]:assert sha(p)==manifest['bindings'][p]
  data[row['case'],row['horizon']]=list(map(json.loads,Path(row['target_file']).open()));features[row['case']]={r['id']:r for r in map(json.loads,Path(row['ready_feature_file']).open())}
 pred={(p['case'],p['horizon'],p['id']):p for p in x['predictions']};assert len(pred)==len(x['predictions'])==178560;checks=0
 for fold in x['fits']:
  episode=fold['heldout_episode'];train=sorted(c for c in features if c.split('/')[1]!=episode);test=sorted(set(features)-set(train));assert train==fold['train_cases'] and test==fold['test_cases'];pool=defaultdict(lambda:[0,0,0,0]);cells=defaultdict(lambda:[0,0,0,0])
  for case in train:
   for h in [1,2]:
    for row in data[case,h]:
     f=features[case][row['id']];key=h,f['occupancy'],f['acc_bits'],f['Q'];a=num(f['acc_bits'])
     for q in row['joint']:
      delta=num(q['acc_bits'])-a;other=q['F_other'];n=q['calls'];values=[n,n*delta,n*other,n*delta*other]
      for table,k in [(pool,(h,)),(cells,key)]:
       for j,v in enumerate(values):table[k][j]+=v
  assert dict(pool)=={tuple(r['key']):r['sums'] for r in fold['pooled']};assert dict(cells)=={tuple(r['key']):r['sums'] for r in fold['cells']}
  for case in test:
   for h in [1,2]:
    losses=defaultdict(F);nodes=defaultdict(F);calls=queried=missing=0
    for row in data[case,h]:
     f=features[case][row['id']];key=h,f['occupancy'],f['acc_bits'],f['Q'];n,d,o,do=cells.get(key,pool[h,]);a=num(f['acc_bits']);expected=dict(joint=F(a*o+do,n),product=F((a*n+d)*o,n*n),known_history=F(a*o,n));p=pred[case,h,row['id']];assert p['observed_calls']==row['calls'];assert expected=={m:F(*v) for m,v in p['predicted_AF'].items()}
     if h==1:assert len(set(expected.values()))==1
     if not row['calls']:missing+=1;continue
     queried+=1;calls+=row['calls'];mean=F(sum(num(q['acc_bits'])*q['F_other']*q['calls'] for q in row['joint']),row['calls'])
     for m,v in expected.items():
      nodes[m]+=(v-mean)**2
      for q in row['joint']:losses[m]+=q['calls']*(v-num(q['acc_bits'])*q['F_other'])**2
    score=next(s for s in x['scores'] if (s['case'],s['horizon'])==(case,h));assert (calls,queried,missing)==(score['calls'],score['queried_resources'],score['no_query_resources'])
    for m in losses:assert math.isclose(float(losses[m]/calls),score['metrics'][m]['call_MSE'],abs_tol=1e-12,rel_tol=1e-12);assert math.isclose(float(nodes[m]/queried),score['metrics'][m]['queried_resource_mean_MSE'],abs_tol=1e-12,rel_tol=1e-12)
    checks+=1
 out=dict(status='ALL178560_PREDICTIONS_TRAIN_HISTOGRAMS_AND12_SCORES_RECONCILED',frames=checks,scope='Independent joint-entry train residual sums and percall squared losses;known-history firstwindow identity exact. No-query rows retain mask.',bindings={str(p):sha(p) for p in [D/'evaluation_v1.json',Path(__file__)]})
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(out['status'])
if __name__=='__main__':main()
