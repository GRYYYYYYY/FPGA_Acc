"""All logged iterations and exact policy/input matching, scoped native outcomes."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/sha1_native_abort_policy_v1_2026-10-10';rp=D/'receipt.json';r=json.loads(rp.read_text());pp=D/'protocol.json';p=json.loads(pp.read_text());assert r['all_cases_attempted'] and [x['width'] for x in r['rows']]==[32,64,96]
bindings={**r['bindings'],str(rp):sha(rp),str(pp):sha(pp),**closure([Path(__file__)])};assert all(sha(k)==h for k,h in bindings.items());rows=[]
for row,case in zip(r['rows'],p['cases']):
 width=row['width'];assert width==case['width'];cmd=case['command'];assert cmd[cmd.index('--max_router_iterations')+1]=='100' and cmd[cmd.index('--routing_failure_predictor')+1]=='off' and cmd[cmd.index('--router_init_wirelength_abort_threshold')+1]=='1000000000';assert cmd[cmd.index('--route_chan_width')+1]==str(width)
 for k,h in row['files'].items():assert sha(k)==h;bindings[k]=h
 text=(D/str(width)/'native.log').read_text();assert 'RouterOpts.routing_failure_predictor = OFF' in text and 'RouterOpts.init_wirelength_abort_threshold: 1000000000.000000' in text and 'Completed placement consistency check successfully.' in text
 assert 'Routing aborted,' not in text and 'fail routing.' not in text
 start=text.index('Iter   Time');part=text[start:];iterations=[];last_over=None
 for line in part.splitlines():
  m=re.match(r'^\s*(\d+)\s+[\d.]+\s+[\d.]+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)\s+\(',line)
  if m:iterations.append(int(m[1]));last_over=int(m[2])
 assert iterations==list(range(1,len(iterations)+1)) and iterations
 if row['exit_code']==2:
  assert len(iterations)==100 and last_over>0 and 'Routing failed.' in text and 'VPR failed to implement circuit' in text
  status='NATIVE_100_ITERATION_BUDGET_FAILURE'
 else:
  assert row['exit_code']==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text and last_over==0
  assert int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1])==len(iterations);status='NATIVE_FULL_SUCCESS_PENDING_INDEPENDENT_ROUTE_AUDIT'
 rows.append(dict(width=width,status=status,logged_iterations=len(iterations),last_printed_overused_rr_nodes=last_over,mathematical_infeasibility_proved=False))
assert all(sha(k)==h for k,h in bindings.items())
(D/'outcome_verification_v1.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_three_policy_iterations_and_native_outcomes_verified=True,scope='Exposed same-design finite100 native budget labels under predictorOFF/threshold1e9 with exact original graph/fixed input hashes. No early abort observed. Not mathematical infeasibility, family heldout, model classifier, success canonical closure or full-cost speedup proof.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
