"""Authenticate native first-round zero history and estimator update timing."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10'
bindings=closure([Path(__file__)])
for name in ['verification.json','common_state_projection_verification_v1.json']:
 p=D/name;v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
p=D/'states/round_1.tsv';assert str(p) in bindings and sha(p)==bindings[str(p)]
seen=set();overuse_nodes=overuse_units=nonunit_history=0;hist=Counter()
with p.open() as f:
 header=f.readline().split();assert header==['H','1','0','0']
 for line in f:
  a=line.split()
  if a[0]!='N':continue
  n,occ,cap=int(a[1]),int(a[2]),int(a[3]);assert n not in seen;seen.add(n);hist[a[4]]+=1
  nonunit_history+=float(a[4])!=1.;overuse_nodes+=occ>cap;overuse_units+=max(0,occ-cap)
assert len(seen)==904438 and nonunit_history==0
M=R/'experiments/mmc_observed_round2_full_schedule_v1_2026-10-12/model'
receipt=json.loads((M/'receipt.json').read_text());assert all(sha(k)==h for k,h in receipt['bindings'].items());assert all(sha(k)==h for k,h in receipt['files'].items());bindings.update(receipt['bindings']);bindings.update(receipt['files']);bindings[str(M/'receipt.json')]=sha(M/'receipt.json')
rows=receipt['rounds'];assert len(rows)==2
assert all(sha(k)==h for k,h in bindings.items())
result=dict(bindings=bindings,native_first_round=dict(nodes=len(seen),history_histogram=dict(hist),nonunit_history=nonunit_history,overuse_nodes=overuse_nodes,overuse_units=overuse_units,acc_factor=0),estimator_initial_overflow=rows[0]['overflow_before'],estimator_first_round_overflow=rows[0]['overflow_after'],finding='Native first-round end has all accumulated costs equal to 1 despite congestion. Estimator producer updates history from initial occupancy before its first feedback search and again from round0 before round1; different starting routes prevent nodewise causal attribution.',scope='Authenticated state and source-timing diagnostic, no quality improvement or native-equivalence proof.')
(D/'first_round_history_diagnosis_v1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'}),flush=True)
