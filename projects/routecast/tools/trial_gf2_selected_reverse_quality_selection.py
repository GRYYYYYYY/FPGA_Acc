"""Whole cohort fresh quality-selected FULL reload, candidate and fallback branches."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_selected_reverse_quality_selection_2026-10-06';out.mkdir();cases=[]
for w,count in ((32,264),(64,491),(128,908)):
 stem=f'gf2_d{w}_selected_reverse_quality_gate';names=[]
 for kind in ('trial','verify'):
  s=(root/'tools'/f'{kind}_ex5p_live_staged_quality_gate.py').read_text().replace('ex5p_live_staged_quality_gate',stem).replace('ex5p_swapped_reference_canonical_reload',f'gf2_d{w}_fixed_original_reference_canonical_reload').replace('ex5p_live_staged_canonical_reload',f'gf2_d{w}_selected_reverse_canonical_reload').replace('1916',str(count))
  if kind=='verify':
   s=s.replace("expected==r['selected']=='reference'","expected==r['selected']").replace("==r['reference_cpd_ns']","==r[expected+'_cpd_ns']").replace("'rejected_predicted_timing_regression':True","'rejected_predicted_timing_regression':expected=='reference'").replace("'selected_reference_files_exact':True","'selected_files_exact':True")
  name=f'{kind}_{stem}.py';(root/'tools'/name).write_text(s);names.append(name)
 cases.append({'width':w,'tools':names,'source_sha256':{n:sha(root/'tools'/n) for n in names}})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'scope':'CPD nonregression against matched cold reference, fresh original native FULL zero-fixup reload of each selected bundle; no concurrent/durable publication.'},indent=2)+'\n');rows=[]
for c in cases:
 stages=[]
 for name in c['tools']:
  t=time.monotonic();log=out/name.replace('.py','.log')
  with log.open('w') as f:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)})
  if code:break
 rows.append({'width':c['width'],'stages':stages});print(c['width'],[s['exit_code'] for s in stages],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':True},indent=2)+'\n')
