"""Exact rank-sum/AUC and rank-dispersion decomposition of binary-label Spearman."""
import json,math,struct,hashlib
from pathlib import Path
from fractions import Fraction
from audit_prince_forecast_metrics_v1 import ranks2
R=Path(__file__).resolve().parents[1];S=R/'experiments/prince_full_resource_history_v1_2026-10-20';D=R/'experiments/prince_history_rank_split_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def prob(w):return Fraction(struct.unpack('<f',struct.pack('<I',w))[0])
v=load(S/'verification.json');rows=[]
for row in v['rows']:
 if row['status']!='SCORED':continue
 c=row['case'];spec=load(R/'experiments/prince_feedback_quality_v1_2026-10-20'/c/'specification.json');truth={int(n):y for n,y in load(spec['label_physical_audit'])['node_occupancy'].items()};scores=list(map(json.loads,(S/c/'expected_counts.jsonl').open()));ys=[truth.get(x['id'],0) for x in scores];n=len(ys);p=sum(ys);z=n-p;methods={}
 for name in ['B_only','BH']:
  vals=[prob(x['B_word' if name=='B_only' else 'BH_word']) for x in scores];r=ranks2(vals);positive_sum=sum(a for a,y in zip(r,ys) if y);negative_sum=sum(a for a,y in zip(r,ys) if not y);gap=Fraction(positive_sum,p)-Fraction(negative_sum,z);variance=Fraction(sum((a-(n-1))**2 for a in r),n);rho=float(gap)*math.sqrt(p*z/(n*n))/math.sqrt(float(variance));assert abs(rho-row['metrics'][name]['resource']['spearman'])<1e-14
  auc=Fraction(positive_sum-p*(p-1),2*p*z)
  # Separate pair-count computation, with half credit for tied scores.
  groups={}
  for a,y in zip(vals,ys):
   if a not in groups:groups[a]=[0,0]
   groups[a][y]+=1
  below=0;twicewins=0
  for a,(neg,pos) in sorted(groups.items()):twicewins+=pos*(2*below+neg);below+=neg
  assert auc==Fraction(twicewins,2*p*z)
  methods[name]=dict(auc=float(auc),positive_negative_doubled_rank_gap=float(gap),doubled_rank_stddev=math.sqrt(float(variance)),reconstructed_spearman=rho)
 rows.append(dict(case=c,methods=methods));print(c,{name:(m['auc'],m['doubled_rank_stddev']) for name,m in methods.items()})
with (D/'rank_decomposition_v1.json').open('x') as f:json.dump(dict(status='EXACT_RANK_SUM_AND_PAIR_COUNT_RECONCILED',rows=rows,source_sha256=hashlib.sha256((S/'verification.json').read_bytes()).hexdigest(),auditor_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),scope='Exposed diagnosis; AUC not substituted for original metrics.'),f,indent=2);f.write('\n')
