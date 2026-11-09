"""Frozen whole muxfamily ABC LUT6 mapping and equivalence evidence."""
import json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments/mux_crossbar_family_freeze_2026-10-06';r=json.loads((base/'receipt.json').read_text());p=json.loads((base/'protocol.json').read_text());assert r['protocol_sha256']==sha(base/'protocol.json');original=json.loads((root/'experiments/gf2_recurrence_family_freeze_2026-10-06/protocol.json').read_text());abc=next(Path(f) for f in original['native_inputs_sha256'] if Path(f).name=='abc');assert sha(abc)==original['native_inputs_sha256'][str(abc)];out=root/'experiments/mux_crossbar_frontend_2026-10-06';out.mkdir();cases=[]
for row in r['rows']:
 w=row['width'];src=base/f'w{w}/generated.blif';assert sha(src)==row['generated_blif_sha256'];d=out/f'w{w}';d.mkdir();target=d/'design.blif';cases.append({'width':w,'source':str(src),'source_sha256':sha(src),'target':str(target),'mapping_command':[str(abc),'-c',f'read_blif {src}; strash; if -K 6; write_blif {target}'],'cec_command':[str(abc),'-c',f'cec {src} {target}']})
(out/'protocol.json').write_text(json.dumps({'cases':cases,'abc_sha256':sha(abc),'family_receipt_sha256':sha(base/'receipt.json'),'source_sha256':sha(Path(__file__)),'scope':'All3siblings LUT6 mapping andCEC, no native routing or thresholdtuning.'},indent=2)+'\n');rows=[]
for c in cases:
 d=Path(c['target']).parent;stages=[]
 for kind in ('mapping','cec'):
  t=time.monotonic();log=d/f'{kind}.log'
  with log.open('w') as f:code=subprocess.run(c[kind+'_command'],stdout=f,stderr=subprocess.STDOUT,cwd=root,timeout=180).returncode
  assert code==0
  if kind=='cec':assert 'Networks are equivalent' in log.read_text()
  stages.append({'kind':kind,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)})
 target=Path(c['target']);luts=sum(x.startswith('.names ') for x in target.read_text().splitlines());rows.append({'width':c['width'],'LUTs':luts,'mapped_sha256':sha(target),'stages':stages,'equivalent':True});print(c['width'],luts,'CEC passes',flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':True},indent=2)+'\n')
