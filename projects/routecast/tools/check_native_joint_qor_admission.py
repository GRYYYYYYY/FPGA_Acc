"""Boundary/tie/rejection checks for the new exact native admission policy."""
import json
from pathlib import Path
from native_joint_qor_admission import decide
from pre_route_endpoints import sha
reference={'cpd_ns':'2','wirelength':10}
assert decide(None,reference)['selected']=='reference'
for c,w,selected in [('2',10,'candidate'),('1999999999999999999999/1000000000000000000000',10,'candidate'),('2000000000000000000001/1000000000000000000000',10,'reference'),('1',11,'reference'),('3',9,'reference'),('1',9,'candidate')]:
 assert decide(dict(cpd_ns=c,wirelength=w),reference)['selected']==selected
invalid=[dict(cpd_ns='nan',wirelength=1),dict(cpd_ns='inf',wirelength=1),dict(cpd_ns='-1',wirelength=1),dict(cpd_ns=True,wirelength=1),dict(cpd_ns='1',wirelength=True),dict(cpd_ns='1',wirelength=-1),dict(cpd_ns='1',wirelength=1.0),dict(cpd_ns='1')]
for value in invalid:
 for candidate,ref in [(value,reference),(None,value)]:
  try:decide(candidate,ref)
  except ValueError:pass
  else:raise AssertionError('invalid metrics accepted')
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_joint_qor_admission_contract_2026-10-07';out.mkdir()
(out/'verification.json').write_text(json.dumps(dict(policy_sha256=sha(root/'tools/native_joint_qor_admission.py'),checker_sha256=sha(Path(__file__)),scope='Exact zero-tolerance CPD/wire ties, sub-floating-point regressions, missing candidate and malformed/nonfinite/negative/bool metric rejection. Does not authenticate native source evidence or publish routing state.'),indent=2)+'\n')
print('Exact native joint admission contract passed')
