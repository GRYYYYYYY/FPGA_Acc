"""Independent exact rational metric recomputation for frozen new family."""
import json,math
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/priority_frozen_evaluation_2026-10-07'
def metrics(records,keys,k):
 pairs={key:(F(x['predicted'],x['capacity']),F(x['native'],x['capacity'])) for key,x in zip(keys,records)};assert len(pairs)==len(records);keys=sorted(pairs);k=min(k,len(keys));ps=sorted(keys,key=lambda key:(-pairs[key][0],key))[:k];ts=sorted(keys,key=lambda key:(-pairs[key][1],key))[:k]
 def ranks(col):
  vals=[pairs[key][col] for key in keys];counts={v:vals.count(v) for v in set(vals)};cumulative=0;lookup={}
  for value in sorted(counts):lookup[value]=F(2*cumulative+counts[value]-1,2);cumulative+=counts[value]
  return [lookup[v] for v in vals]
 x,y=ranks(0),ranks(1);mean=F(len(keys)-1,2);sx=sum((v-mean)**2 for v in x);sy=sum((v-mean)**2 for v in y);rho=float(sum((a-mean)*(b-mean) for a,b in zip(x,y)))/math.sqrt(float(sx*sy)) if sx and sy else None
 return dict(spearman=rho,precision_at_k=len(set(ps)&set(ts))/k,recall_at_k=len(set(ps)&set(ts))/k,mae=float(sum(abs(a-b) for a,b in pairs.values())/len(keys)),truth_k_boundary=float(pairs[ts[-1]][1]),prediction_k_boundary=float(pairs[ps[-1]][0]),universe_size=len(keys),k=k)

p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==d for f,d in p['sources'].items()) and all(sha(f)==d for f,d in p['inputs'].items());assert [x['width'] for x in r['rows']]==p['cohort'];rows=[]
for row in r['rows']:
 assert all(sha(f)==d for f,d in row['files'].items());n=row['width']
 if row['prediction'] is None or row['prediction']['failure'] is not None:
  assert row['metrics'] is None or row['metrics']['spatial'] is row['metrics']['concrete'] is None;rows.append(dict(width=n,complete=False));continue
 v=json.loads((out/f'n{n}/vectors.json').read_text())
 for name,records,keys in [('concrete',v['channels'],[x['node'] for x in v['channels']]),('spatial',v['bins'],[tuple(x['key']) for x in v['bins']])]:
  expected=metrics(records,keys,row['metrics'][name]['k'])
  for key,value in expected.items():
   observed=row['metrics'][name][key];assert observed is None if value is None else abs(value-observed)<1e-12,(n,name,key,value,observed)
 rows.append(dict(width=n,complete=True,paths_audited=row['paths_audited'],spatial=row['metrics']['spatial']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Whole new locally generated family: frozen transitive predictor/evaluator/native inputs before label generation, no parameter retuning; originalXML final path/capacity proofs and independent exact rational archived-vector metric recomputation. Not external benchmark generalization, candidate native FULL/STA or full accepted workflow gain.'),indent=2)+'\n');print(rows)
