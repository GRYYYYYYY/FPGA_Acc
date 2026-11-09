"""Prepare/check frozen additional MMC cases; never run native routing."""
import json,sys,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
G=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18'
p=json.loads((G/'cohort_protocol.json').read_text());assert p['case_count']==3 and not p['target_labels_generated']
D=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18';D.mkdir()
rows=[]
for index,protocol in enumerate(p['cases'],1):
 case=Path(protocol).parent;out=D/('case_%02d'%index)
 for stage,args in [('prepare',[str(case),str(out)]),('verify',[str(out)])]:
  script='prepare_mmc_multiplacement_inputs_v1_2026_10_18.py' if stage=='prepare' else 'verify_mmc_multiplacement_inputs_v1_2026_10_18.py'
  print('START',case.name,stage,flush=True)
  code=subprocess.call([sys.executable,str(R/'tools'/script),*args],cwd=R)
  rows.append(dict(case=case.name,stage=stage,exit_code=code))
  (D/'stage_status.json').write_text(json.dumps(rows,indent=2))
  assert code==0
assert not list(D.rglob('*.route'))
with (D/'preparation_complete.json').open('x') as f:json.dump(dict(stages=rows,all3_endpoint_and_native_identity_checks_pass=True,target_routes_generated=False),f,indent=2)
print('ALL3 FROZEN INPUTS VERIFIED; NO ROUTING LABELS',flush=True)
