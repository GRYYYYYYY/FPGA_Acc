"""Bind every frozen development outcome plus fresh native joint-QoR evidence."""
import json,re,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
protocol=ROOT/'experiments/owner_wire_two_weight_development_protocol_2026-10-07.json'
p=read(protocol);bindings={str(protocol):sha(protocol)};cohorts=[];qualified=[]
for item in p['weights']:
 label='50ps' if item['weight_ns']=='1/20' else '100ps';out=ROOT/'experiments'/item['output'];report=out/'development_comparison.json';d=read(report)
 assert d['protocol_sha256']==sha(protocol)
 for f,h in d['bindings'].items():assert sha(f)==h;bindings[f]=h
 bindings[str(report)]=sha(report)
 assert sha(item['producer'])==item['producer_sha256']
 for r in d['rows']:
  if r['status']=='PRIOR_ALLOCATION_SKIP':continue
  work=out/f"w{r['width']}_m{r['index']}"
  for name in ('control_timing','physical_budget','floor','choice','observation','history_cost'):
   f=work/f'{name}_verification.json';v=read(f);assert v['result_sha256']==r['result_sha256'];bindings[str(f)]=sha(f)
  if r['status']!='ACTUAL_MODEL_PASS_NATIVE_PENDING':continue
  w,i=r['width'],r['index'];base=ROOT/f'experiments/mux_owner_wire_{label}_w{w}m{i}_quality_gate_2026-10-07';own=ROOT/f'experiments/mux_owner_wire_{label}_w{w}m{i}_candidate_canonical_2026-10-07'
  gate=read(base/'verification.json');canonical=read(own/'verification.json');gr=read(base/'receipt.json');cr=read(own/'receipt.json')
  assert gate['receipt_sha256']==sha(base/'receipt.json') and canonical['receipt_sha256']==sha(own/'receipt.json')
  assert canonical['gate_verification_sha256']==sha(base/'verification.json') and canonical['connections']==466
  assert not canonical['cold_reference_selected']
  gv=gate['rows'][0];cv=cr['rows'][0]['reload'];assert cv['exit_code']==0 and cv['fixups']==cv['mismatches']==0
  def wire(log):return int(re.findall(r'Total wirelength:\s*(\d+)',Path(log).read_text())[-1])
  logs=[Path(f) for f in cv['files'] if f.endswith('/reload.log')];assert len(logs)==1;log=logs[0];assert sha(log)==cv['files'][str(log)];native_wire=wire(log);assert native_wire==r['unique_wirelength']
  cp=float(canonical['candidate_cpd_ns'].split('/')[0])/float(canonical['candidate_cpd_ns'].split('/')[1]) if '/' in canonical['candidate_cpd_ns'] else float(canonical['candidate_cpd_ns'])
  reference=float(gv['reference_cpd_ns']);assert cp<=reference and native_wire<=r['cold_wirelength']
  for directory in (base,own):
   for name in ('protocol.json','receipt.json','verification.json'):f=directory/name;bindings[str(f)]=sha(f)
  bindings[str(log)]=sha(log)
  qualified.append(dict(weight=label,width=w,index=i,candidate_cpd_ns=cp,cold_reference_cpd_ns=reference,candidate_wirelength=native_wire,cold_wirelength=r['cold_wirelength'],wire_delta_to_cold=native_wire-r['cold_wirelength'],strict_joint_qor_nonregression=True,accepted_lifecycle_status='NOT_MEASURED',native_gate_verification=str(base/'verification.json'),candidate_own_canonical_verification=str(own/'verification.json')))
 cohorts.append(dict(weight=label,outcomes=dict(Counter(x['status'] for x in d['rows'])),all_outcomes=str(report)))
assert len(qualified)==3
out=ROOT/'experiments/owner_wire_two_weight_development_final_2026-10-07';out.mkdir(exist_ok=True)
(out/'evidence.json').write_text(json.dumps(dict(protocol_sha256=sha(protocol),finalizer_sha256=sha(Path(__file__)),bindings=bindings,cohorts=cohorts,fresh_native_joint_qor_candidates=qualified,scope='Prespecified two-weight SAME-MUX-family development; all24 outcomes retained, six independent audits per searched case. Three complete modelPASS candidates fresh native CPD gate and OWN zero-fixup FULLSTA, XML NET-union wire equals candidate native logs, cold union matches authenticated archived cold native logs. Strict joint QoR is retrospective comparison, not a predeclared deployed admission policy. No selected-state publication, full accepted-lifecycle timing, heldout generalization or hardware claim.'),indent=2)+'\n')
print(qualified,flush=True)
