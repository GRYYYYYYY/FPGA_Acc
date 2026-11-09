"""Whole frozen GF2 family candidate native validation; no width/parameter tuning."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments/gf2_recurrence_joint_transfer_2026-10-06';r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/gf2_recurrence_native_import_2026-10-06';out.mkdir();frozen=[]
for record,audited in zip(r['rows'],v['rows']):
 width=record['width'];count=record['required_connections'];directory=base/f'gf2_d{width}';assert record['candidate_sha256']==audited['original_candidate_sha256']==sha(directory/'receipt.json');assert audited['accepted_paths_checked']==count
 # Expose independently verified original-candidate binding for reusable serializer.
 (directory/'verification.json').write_text(json.dumps({'receipt_sha256':record['candidate_sha256'],'accepted_paths_checked':count,'independent_audit_verification_sha256':audited['audit_verification_sha256']},indent=2)+'\n')
 stem=f'gf2_d{width}_native_import';names=[]
 for kind in ('trial','verify'):
  s=(root/'tools'/f'{kind}_tseng_joint_native_import.py').read_text().replace('tseng_joint_native_import',stem).replace('experiments/tseng_joint_transfer_2026-10-06',str(directory.relative_to(root))).replace('experiments/nonzero_rc_tseng_endpoints_2026-10-06',str(directory.relative_to(root))).replace('work/nonzero_rc_tseng_reference128_2026-10-06',f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}').replace('experiments/nonzero_rc_tseng_reference128_2026-10-06',f'experiments/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}').replace('1234',str(count)).replace('tseng','gf2_frozen_family')
  name=f'{kind}_{stem}.py';(root/'tools'/name).write_text(s);names.append(name)
 frozen.append({'width':width,'count':count,'tools':names,'source_sha256':{n:sha(root/'tools'/n) for n in names}})
p={'cases':frozen,'parent_receipt_sha256':sha(base/'receipt.json'),'parent_verification_sha256':sha(base/'verification.json'),'scope':'Whole prospective locally generated family with frozen policy. Packed identity/serialization/nativeFULLSTA and independent selected-path audit on all candidates; keep outcomes, no model tuning.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[]
for case in frozen:
 stages=[]
 for name in case['tools']:
  t=time.monotonic();log=out/name.replace('.py','.log')
  with log.open('w') as stream:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)})
  if code:break
 record={'width':case['width'],'stages':stages};directory=root/'experiments'/f"gf2_d{case['width']}_native_import_2026-10-06"
 if (directory/'receipt.json').exists():
  q=json.loads((directory/'receipt.json').read_text());record.update(candidate_receipt_sha256=sha(directory/'receipt.json'),native_success=q['native_success'],candidate_cpd_ns=q['cpd_ns'])
 if (directory/'verification.json').exists():
  proof=json.loads((directory/'verification.json').read_text());record.update(verification_sha256=sha(directory/'verification.json'),reference_cpd_ns=proof['reference_cpd_ns'])
 rows.append(record);print(record['width'],record.get('candidate_cpd_ns'),record.get('reference_cpd_ns'),[s['exit_code'] for s in stages],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':True},indent=2)+'\n')
