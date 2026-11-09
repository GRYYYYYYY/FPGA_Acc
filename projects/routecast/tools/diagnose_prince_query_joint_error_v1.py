"""Label-dependent factor oracles for error attribution only."""
import json,struct
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_query_joint_prediction_v1_2026-10-20';S=E/'prince_future_query_joint_v1_2026-10-20'
def load(p):return json.loads(p.read_text())
def val(w):return round(struct.unpack('<f',int(w).to_bytes(4,'little'))[0])
def main():
 x=load(D/'evaluation_v1.json');pred={(p['case'],p['horizon'],p['id']):p for p in x['predictions']};rows=[]
 for row in load(S/'dataset_manifest.json')['rows']:
  if row['status']!='FUTURE_QUERY_LABELS_EXTRACTED':continue
  features={r['id']:r for r in map(json.loads,Path(row['ready_feature_file']).open())};totals={m:F(0) for m in ['constant_perresource_oracle_floor','oracle_A_with_predicted_F','oracle_meanF_with_ready_A','known_history']};calls=0
  for r in map(json.loads,Path(row['target_file']).open()):
   n=r['calls']
   if not n:continue
   calls+=n;a0=val(features[r['id']]['acc_bits']);m=r['moment_sums'];a=F(m['A'],n);other=F(m['F_other'],n);mean=F(m['A_F_other'],n);assert mean==a*other;p=F(*pred[row['case'],row['horizon'],r['id']]['predicted_AF']['known_history']);ef=p/a0;second=sum((val(q['acc_bits'])*q['F_other'])**2*q['calls'] for q in r['joint']);variance=second-n*mean*mean;assert variance>=0;estimates=dict(constant_perresource_oracle_floor=mean,oracle_A_with_predicted_F=a*ef,oracle_meanF_with_ready_A=a0*other,known_history=p)
   for name,z in estimates.items():
    loss=second-2*z*m['A_F_other']+n*z*z;assert loss==variance+n*(z-mean)**2;totals[name]+=loss
  rows.append(dict(case=row['case'],horizon=row['horizon'],calls=calls,MSE={m:float(t/calls) for m,t in totals.items()}))
 summary={}
 for h in [1,2]:
  a=[r for r in rows if r['horizon']==h];n=sum(r['calls'] for r in a);summary[str(h)]={m:sum(r['MSE'][m]*r['calls'] for r in a)/n for m in a[0]['MSE']}
 out=dict(status='EXACT_PERRESOURCE_VARIANCE_DECOMPOSITION_AND_FACTOR_ORACLES',rows=rows,summary=summary,scope='Retrospective label-dependent diagnostic references,not deployable forecasts or replacement gates. Variance floor applies to one constant perresource/horizon forecast only;query-context-aware predictor may reduce it.',bindings={str(p):sha(p) for p in [D/'evaluation_v1.json',S/'dataset_manifest.json',Path(__file__)]})
 with (D/'factor_error_diagnosis_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(summary)
if __name__=='__main__':main()
