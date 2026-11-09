"""Recompute metrics from archived vectors with independent exact rational ranks."""
import json,math
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_resource_prediction_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(ROOT/'tools'/n)==h for n,h in p['sources_sha256'].items());assert [x['width'] for x in r['rows']]==[4,8,16];assert p['audit_sha256']==sha(ROOT/'experiments/bitonic_owner_union_prediction_2026-10-07/verification.json')
def metrics(records,keys,k):
 pairs={key:(F(x['predicted'],x['capacity']),F(x['native'],x['capacity'])) for key,x in zip(keys,records)};assert len(pairs)==len(records);keys=sorted(pairs);k=min(k,len(keys));ps=sorted(keys,key=lambda key:(-pairs[key][0],key))[:k];ts=sorted(keys,key=lambda key:(-pairs[key][1],key))[:k]
 def ranks(col):
  vals=[pairs[key][col] for key in keys];counts={v:vals.count(v) for v in set(vals)};cumulative=0;lookup={}
  for value in sorted(counts):lookup[value]=F(2*cumulative+counts[value]-1,2);cumulative+=counts[value]
  return [lookup[v] for v in vals]
 x,y=ranks(0),ranks(1);mean=F(len(keys)-1,2);sx=sum((v-mean)**2 for v in x);sy=sum((v-mean)**2 for v in y);rho=float(sum((a-mean)*(b-mean) for a,b in zip(x,y)))/math.sqrt(float(sx*sy)) if sx and sy else None
 return dict(spearman=rho,precision_at_k=len(set(ps)&set(ts))/k,recall_at_k=len(set(ps)&set(ts))/k,mae=float(sum(abs(a-b) for a,b in pairs.values())/len(keys)),truth_k_boundary=float(pairs[ts[-1]][1]),prediction_k_boundary=float(pairs[ps[-1]][0]),universe_size=len(keys),k=k)
for case,row in zip(p['cases'],r['rows']):
 assert case['width']==row['width'];assert all(sha(case[name])==case[name+'_sha256'] for name in ('candidate','graph','native_route'))
 if row['width']==16:assert row['spatial'] is row['concrete'] is None and row['completed_connections']==108 and row['required_connections']==5070;continue
 file=out/f"bitonic_n{row['width']}_vectors.json";assert sha(file)==row['vector_sha256'];v=json.loads(file.read_text())
 for name,records,keys in [('concrete',v['channels'],[x['node'] for x in v['channels']]),('spatial',v['bins'],[tuple(x['key']) for x in v['bins']])]:
  expected=metrics(records,keys,row[name]['k'])
  for key,value in expected.items():assert value==row[name][key] if value is None else abs(value-row[name][key])<1e-12,(name,key,value,row[name][key])
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),counts=[4,8,16],complete_case_metrics_recomputed=2,incomplete_case_retained=True,scope='Archivedvector exact-rational ranks/topsets independently recomputed, source/input/vector/audit bindings checked. Descriptive complete-case metrics only, no allcohortaccuracy/nativeQoR/gain or strictholdout claim.'),indent=2)+'\n');print('Bitonic allcase metrics independently recomputed')
