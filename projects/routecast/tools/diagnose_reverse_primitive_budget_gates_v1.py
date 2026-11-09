"""Inspect exact original floor-derived budget decisions after primitive audit."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];D=R/'experiments/real_rr_reverse_single_sink_v1_2026-10-08'/name
def load(p):return json.loads(p.read_text())
v=load(D/'verification.json');assert v['complete_single_target_primitive_pass']
assert all(sha(p)==h for p,h in v['bindings'].items())
r=load(D/'receipt.json');p=load(D/'protocol.json')
ep=load(next(Path(k) for k in r['bindings'] if k.endswith('/endpoints.json')))
groups=defaultdict(list)
for q in ep['connections']:groups[q['net_id']].append(q)
selected={n:qs for n,qs in groups.items() if len({q['sink'] for q in qs})==1}
initial=load(D/'initial.json');budgets={}
for n in selected:
 a,b=initial['baseline'][str(n)],initial['candidate'][str(n)]
 assert a['delay']==b['delay']==a['objective']==b['objective']
 budgets[n]=max(p['scale']//10**9,(3*a['delay']+1)//2)
rows=[]
for phase in ['initial','round0','round1']:
 data=load(D/(phase+'.json'));gates=Counter();delay_changes=Counter();examples=[]
 for n in selected:
  a,b=data['baseline'][str(n)],data['candidate'][str(n)]
  assert a['objective']==b['objective']
  forward_safe=a['delay']<=budgets[n];reverse_safe=b['delay']<=budgets[n]
  gates[f'forward_{forward_safe}_reverse_{reverse_safe}']+=1
  delta=b['delay']-a['delay'];delay_changes['equal' if delta==0 else 'higher' if delta>0 else 'lower']+=1
  if forward_safe!=reverse_safe:examples.append(dict(net_id=n,baseline_delay=a['delay'],candidate_delay=b['delay'],budget=budgets[n],objective=a['objective'],connection_ids=[q['connection_id'] for q in selected[n]]))
 rows.append(dict(phase=phase,complete_nets=len(selected),budget_gate_pairs=dict(gates),candidate_raw_delay_changes=dict(delay_changes),gate_change_examples=examples))
bindings={**v['bindings'],str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(p)==h for p,h in bindings.items())
(D/'budget_gate_diagnosis_v1.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Original max(1ns,ceil1.5floor) admission applied to audited complete primitive paths under frozen old prices. Counterfactual gates only, not a new prospective feedback ledger or native route. Equal weighted objective need not imply equal raw RC or budget admission.'),indent=2)+'\n')
print(json.dumps([{k:val for k,val in row.items() if k!='gate_change_examples'} for row in rows],indent=2))
