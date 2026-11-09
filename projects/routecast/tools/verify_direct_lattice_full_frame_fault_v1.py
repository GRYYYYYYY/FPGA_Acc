"""Isolated wrong lattice scalar must be rejected by a complete real frame."""
import json,runpy,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
if len(sys.argv)>1 and sys.argv[1]=='child':
 import exact_rc_lattice_direct_pairs_v2 as lattice
 old=lattice.exact_scale
 def wrong(*args):
  scale,pairs=old(*args);print('INJECT WRONG LATTICE SCALAR',flush=True);return scale+1,pairs
 lattice.exact_scale=wrong
 model,target=sys.argv[2:4]
 script=R/'tools/verify_resident_demand_frame_direct_lattice_v7.py'
 sys.argv=[str(script),model,'initial',target]
 runpy.run_path(str(script),run_name='__main__')
 raise AssertionError('wrong scale accepted')
model=R/'experiments/xtea_actual_old_linear_budget_index_v1_2026-10-10/model'
admission=model.parent/'verification.json';v=json.loads(admission.read_text())
assert v['complete_independent_physical_and_actual_old_events_pass'] and all(sha(p)==h for p,h in v['bindings'].items())
D=R/'experiments/direct_lattice_full_frame_fault_v1_2026-10-10';D.mkdir()
bindings={**closure([Path(__file__),R/'tools/verify_resident_demand_frame_direct_lattice_v7.py']),str(admission):sha(admission)}
for name in ['receipt.json','protocol.json','initial.json','floors.json']:
 p=model/name;bindings[str(p)]=sha(p)
target=D/'should_not_exist.json';log=D/'fault.log'
with log.open('w') as f:
 p=subprocess.run([sys.executable,str(Path(__file__)),'child',str(model),str(target)],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=300)
text=log.read_text();assert p.returncode!=0 and 'INJECT WRONG LATTICE SCALAR' in text and 'AssertionError' in text
assert 'assert integer.denominator==1' in text and not target.exists()
assert all(sha(p)==h for p,h in bindings.items())
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,files={str(log):sha(log)},exit_code=p.returncode,wrong_exact_scale_rejected_by_actual_full_frame_delay_assertion=True,no_success_proof_created=True,scope='Full frozen XTEA initial frame with isolated in-memory wrong lattice scalar. No source/input mutation. Not MMC full event fault coverage or performance evidence.'),indent=2)+'\n')
print('PASS complete real XTEA frame rejects wrong lattice scalar')
