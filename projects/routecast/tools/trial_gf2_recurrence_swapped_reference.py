"""Frozen same-placement cold controls for all three genuine swaps."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_recurrence_swapped_reference_2026-10-06';out.mkdir();cases=[]
for width in (32,64,128):
 stem=f'gf2_d{width}_swapped_place_cold';tools=[]
 for kind in ('trial','verify'):
  s=(root/'tools'/f'{kind}_tseng_swapped_place_cold.py').read_text().replace('tseng_swapped_place_cold',stem).replace('experiments/tseng_placement_swap_2026-10-06',f'experiments/gf2_d{width}_placement_swap_2026-10-06').replace('work/nonzero_rc_tseng_reference128_2026-10-06',f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}').replace('experiments/nonzero_rc_tseng_reference128_2026-10-06',f'experiments/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}')
  candidate=json.loads((root/f'experiments/gf2_recurrence_placement_updates_2026-10-06/gf2_d{width}/receipt.json').read_text());s=s.replace('1234',str(candidate['required_connections']));name=f'{kind}_{stem}.py';(root/'tools'/name).write_text(s);tools.append(name)
 cases.append({'width':width,'tools':tools,'sources_sha256':{name:sha(root/'tools'/name) for name in tools}})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'policy':'same preNET, swappedplace, originalRR, route-only originalVPR width128/seed1/workers1/max100/timeout180; whole family retained; native labels evaluator only'},indent=2)+'\n');rows=[]
for case in cases:
 stages=[]
 for name in case['tools']:
  t=time.monotonic();log=out/name.replace('.py','.log')
  with log.open('w') as stream:code=subprocess.run(['python3',str(root/'tools'/name)],cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)})
  if code:break
 directory=root/f"experiments/gf2_d{case['width']}_swapped_place_cold_2026-10-06";q=json.loads((directory/'receipt.json').read_text());rows.append({'width':case['width'],'native_success':q['native_success'],'cpd_ns':q['cpd_ns'],'native_process_wall_s':q['native_process_wall_s'],'receipt_sha256':sha(directory/'receipt.json'),'stages':stages});print(case['width'],q['native_success'],q['cpd_ns'],flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_three_retained':True},indent=2)+'\n')
