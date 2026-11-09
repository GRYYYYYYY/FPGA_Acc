"""Canonical native fallback reference evidence for the entire GF2 swap cohort."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_swapped_reference_canonical_2026-10-06';out.mkdir();cases=[]
for w,count in ((32,264),(64,491),(128,908)):
 names=[]
 for kind in ('trial','verify'):
  s=(root/'tools'/f'{kind}_tseng_swapped_reference_canonical_reload.py').read_text().replace('tseng_swapped_reference_canonical_reload',f'gf2_d{w}_swapped_reference_canonical_reload').replace('tseng_swapped_place_cold',f'gf2_d{w}_swapped_place_cold').replace('tseng_swapped_native_import',f'gf2_d{w}_native_seeded_native_import').replace('1234',str(count))
  name=f'{kind}_gf2_d{w}_swapped_reference_canonical_reload.py';(root/'tools'/name).write_text(s);names.append(name)
 cases.append({'width':w,'connections':count,'tools':names,'source_sha256':{n:sha(root/'tools'/n) for n in names},'reference_receipt_sha256':sha(root/f'experiments/gf2_d{w}_swapped_place_cold_2026-10-06/receipt.json')})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'scope':'All three originalVPR cold fallback references captured, postNET/pin canonical remapped and original FULL zero-fixup reload; keep outcomes. No quality publication or runtime claim.'},indent=2)+'\n');rows=[]
for c in cases:
 stages=[]
 for name in c['tools']:
  t=time.monotonic();log=out/name.replace('.py','.log')
  with log.open('w') as f:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)})
  if code:break
 row={'width':c['width'],'stages':stages};d=root/f"experiments/gf2_d{c['width']}_swapped_reference_canonical_reload_2026-10-06"
 for n in ('receipt.json','verification.json'):
  if (d/n).exists():row[n]=json.loads((d/n).read_text());row[n+'_sha256']=sha(d/n)
 rows.append(row);(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==len(cases)},indent=2)+'\n');print(c['width'],[s['exit_code'] for s in stages],flush=True)
