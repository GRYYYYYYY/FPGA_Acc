"""Canonical zero-fixup reload of the complete frozen updated GF2 cohort."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1]
parent=root/'experiments/gf2_recurrence_native_seeded_native_import_2026-10-06'
r=json.loads((parent/'receipt.json').read_text());assert r['all_cases_retained']
out=root/'experiments/gf2_recurrence_native_seeded_canonical_reload_2026-10-06';out.mkdir();cases=[]
for row in r['rows']:
 width=row['width'];count=row['receipt.json']['connections'];assert all(x['exit_code']==0 for x in row['stages'])
 names=[]
 for kind in ('trial','verify'):
  s=(root/'tools'/f'{kind}_tseng_joint_canonical_reload.py').read_text().replace('tseng_joint_canonical_reload',f'gf2_d{width}_native_seeded_canonical_reload').replace('tseng_joint_native_import',f'gf2_d{width}_native_seeded_native_import').replace('experiments/nonzero_rc_tseng_endpoints_2026-10-06',f'experiments/gf2_d{width}_placement_swap_2026-10-06').replace('1234',str(count))
  name=f'{kind}_gf2_d{width}_native_seeded_canonical_reload.py';(root/'tools'/name).write_text(s);names.append(name)
 cases.append({'width':width,'connections':count,'tools':names,'source_sha256':{n:sha(root/'tools'/n) for n in names}})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'parent_receipt_sha256':sha(parent/'receipt.json'),'scope':'All frozen updated candidates, captured pre/post packing sync, unique pin remap and original native FULL zero-fixup reload. All outcomes retained; no publication or speed benefit.'},indent=2)+'\n')
rows=[]
for case in cases:
 stages=[]
 for name in case['tools']:
  t=time.monotonic();log=out/name.replace('.py','.log')
  with log.open('w') as f:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)})
  if code:break
 directory=root/f"experiments/gf2_d{case['width']}_native_seeded_canonical_reload_2026-10-06"
 row={'width':case['width'],'stages':stages}
 for n in ('receipt.json','verification.json'):
  if (directory/n).exists():row[n]=json.loads((directory/n).read_text());row[n+'_sha256']=sha(directory/n)
 rows.append(row);(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==len(cases)},indent=2)+'\n');print(case['width'],[x['exit_code'] for x in stages],flush=True)
