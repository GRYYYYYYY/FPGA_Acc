"""Native FULL/STA validation of every frozen GF2 staged placement candidate."""
import json, subprocess, time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1]
base=root/'experiments/gf2_selected_reverse_updates_2026-10-06'
v=json.loads((base/'verification.json').read_text())
assert v['receipt_sha256']==sha(base/'receipt.json')
out=root/'experiments/gf2_recurrence_selected_reverse_native_import_2026-10-06';out.mkdir()
cases=[]
for row in v['rows']:
 width=row['width'];count=row['accepted_paths_checked'];parent=base/f'gf2_d{width}'
 assert row['receipt_sha256']==sha(parent/'receipt.json')
 local=json.loads((parent/'verification.json').read_text())
 assert local['receipt_sha256']==sha(parent/'receipt.json') and local['accepted_paths_checked']==count
 endpoint=f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{width}'
 stem=f'gf2_d{width}_selected_reverse_native_import';names=[]
 for kind in ('trial','verify'):
  s=(root/'tools'/f'{kind}_tseng_joint_native_import.py').read_text()
  s=s.replace('tseng_joint_native_import',stem).replace('experiments/tseng_joint_transfer_2026-10-06',str(parent.relative_to(root))).replace('experiments/nonzero_rc_tseng_endpoints_2026-10-06',endpoint).replace('work/nonzero_rc_tseng_reference128_2026-10-06',f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}').replace('experiments/nonzero_rc_tseng_reference128_2026-10-06',f'experiments/gf2_d{width}_fixed_original_cold_2026-10-06').replace('1234',str(count))
  if kind=='trial':
   marker="for n in ('design.blif','design.net','design.place'):shutil.copyfile(src/n,work/n)"
   assert marker in s
   # Original placement copied from original native source; reverse target is original.
  name=f'{kind}_{stem}.py';(root/'tools'/name).write_text(s);names.append(name)
 cases.append({'width':width,'connections':count,'tools':names,'sources':{n:sha(root/'tools'/n) for n in names},'candidate_sha256':sha(parent/'receipt.json'),'endpoint_sha256':sha(root/endpoint/'endpoints.json'),'reference_receipt_sha256':sha(root/f'experiments/gf2_d{width}_fixed_original_cold_2026-10-06/receipt.json')})
protocol={'cases':cases,'parent_verification_sha256':sha(base/'verification.json'),'scope':'Entire frozen family retained, unchanged staged estimator policy. Raw selected physical serialization and native FULL/STA versus same-placement cold reference. No canonical zero-fixup or accepted-state publication claim.'}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
rows=[]
for case in cases:
 stages=[]
 for name in case['tools']:
  start=time.monotonic();log=out/name.replace('.py','.log')
  with log.open('w') as f:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-start,'log_sha256':sha(log)})
  if code:break
 row={'width':case['width'],'stages':stages}
 directory=root/f"experiments/gf2_d{case['width']}_selected_reverse_native_import_2026-10-06"
 for filename in ('receipt.json','verification.json'):
  if (directory/filename).exists():row[filename]=json.loads((directory/filename).read_text());row[filename+'_sha256']=sha(directory/filename)
 rows.append(row)
 (out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==len(cases)},indent=2)+'\n')
 print(case['width'],[s['exit_code'] for s in stages],row.get('receipt.json',{}).get('cpd_ns'),flush=True)
