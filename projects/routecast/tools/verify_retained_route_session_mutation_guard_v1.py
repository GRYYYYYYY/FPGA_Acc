"""Change supplied budget during selection; reject before counter advancement."""
import json,tempfile
from unittest.mock import patch
from pathlib import Path
from retained_route_session_v2 import RetainedRouteSession
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/retained_route_session_mutation_guard_v1_2026-10-08';D.mkdir(exist_ok=False)
p=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';case=next(c for c in json.loads(p.read_text())['cases'] if c['width']==8 and c['index']==0)
old=json.loads(Path(case['old']).read_text());session=RetainedRouteSession(case['old'],Path(old['inputs']['graph']['path']).with_name('design.route'))
original_loads=json.loads
with tempfile.TemporaryDirectory(prefix='routecast-retention-guard-') as tmp:
 budget=Path(tmp)/'budget.json';original=Path(case['budget']).read_text();budget.write_text(original);calls=[]
 def changed_loads(text,*args,**kwargs):
  value=original_loads(text,*args,**kwargs)
  if not calls:
   calls.append(1);updated=original_loads(original);updated['default_budget_ns']='1000';budget.write_text(json.dumps(updated))
  return value
 with patch('retained_route_session_v2.json.loads',side_effect=changed_loads):
  try:session.select(case['target'],budget)
  except ValueError as e:assert 'changed during retention' in str(e)
  else:raise AssertionError('Mid-selection budget change accepted')
 assert session.selections==0
 budget.write_text(original);result=session.select(case['target'],budget);assert session.selections==1
 assert len(result['retained'])+len(result['released'])==466
report=dict(bindings={**session.bindings,str(p):sha(p),str(Path(case['target'])):sha(case['target']),str(Path(case['budget'])):sha(case['budget']),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/retained_route_session_v2.py'):sha(R/'tools/retained_route_session_v2.py')},mid_selection_budget_change_rejected=True,selection_counter_unchanged_on_rejection=True,restored_input_recovery_pass=True,scope='Controlled temporary supplied-budget mutation, original workspace inputs unchanged. No native or performance experiment.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS mid-selection change rejected atomically; restored-input selection succeeds')
