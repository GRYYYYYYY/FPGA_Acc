"""Complete prospective hybrid model and independent original-XML state replay."""
import json
import subprocess
import sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
name=sys.argv[1];assert name in ['xtea','8051','mmc']
primitive=R/'experiments/real_rr_bidirectional_single_sink_v2_2026-10-08'/name
primitive_proof=primitive/'verification.json'
v=json.loads(primitive_proof.read_text());assert v['complete_single_target_primitive_pass']
assert all(sha(p)==h for p,h in v['bindings'].items())
budget_proof=primitive/'budget_gate_diagnosis_v1.json'
b=json.loads(budget_proof.read_text());assert all(sha(p)==h for p,h in b['bindings'].items())
P=R/'experiments/resident_radix_count_complete_v4_2026-10-08/protocol.json'
old_protocol=json.loads(P.read_text());assert all(sha(p)==h for p,h in old_protocol['bindings'].items())
endpoint=Path(next(c['endpoint'] for c in old_protocol['cases'] if c['name']==name))
old=R/'experiments/resident_radix_count_complete_v4_2026-10-08'/name
old_receipt=json.loads((old/'receipt.json').read_text())
for section in ['bindings','files']:
    assert all(sha(p)==h for p,h in old_receipt[section].items())
scripts=['run_resident_soft_demand_hybrid_v5.py','verify_resident_demand_frame_physical_v3.py','verify_resident_events_round_schedule_cache_v4.py']
inputs=[P,endpoint,primitive_proof,budget_proof,old/'receipt.json',old/'floors.json']
bindings={**closure([Path(__file__),*[R/'tools'/s for s in scripts]]),**{str(p):sha(p) for p in inputs}}
D=R/'experiments/resident_hybrid_complete_v5_2026-10-08'/name
D.mkdir(parents=True,exist_ok=False);out=D/'resident'
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,name=name,
    scope='Complete original endpoint cohort, prospective new hybrid ledger/prices and two feedback rounds; old zero-price floors compared after model completion, not imported as labels. Independent original XML initial/final state and all committed events replay. No original state/path parity or full workflow performance claim.'),indent=2)+'\n')
commands=[[scripts[0],endpoint,out],[scripts[1],out,'initial'],[scripts[1],out,'sketch'],[scripts[2],out,name,out/'verification.json']]
for stage,args in enumerate(commands):
    assert all(sha(p)==h for p,h in bindings.items())
    with (D/f'stage{stage}.log').open('w') as log:
        result=subprocess.run([sys.executable,str(R/'tools'/args[0]),*[str(x) for x in args[1:]]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:
        (D/'failure.json').write_text(json.dumps(dict(stage=stage,exit_code=result.returncode),indent=2)+'\n')
        raise SystemExit(result.returncode)
    if stage==0:
        assert json.loads((out/'floors.json').read_text())==json.loads((old/'floors.json').read_text())
    print(name,'COMPLETE_STAGE',stage,flush=True)
proofs={}
for file in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
    p=out/file;proof=json.loads(p.read_text())
    for path,h in proof['bindings'].items():assert sha(path)==h
    proofs[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
receipt=json.loads((out/'receipt.json').read_text())
result=dict(bindings=bindings,proofs=proofs,status='COMPLETE_PROSPECTIVE_HYBRID_VERIFIED',
    all_original_zero_price_floors_equal=True,model_paid_seconds=receipt['total_paid_resident_seconds'],
    overflow=[receipt['rounds'][0]['overflow_before'],*[r['overflow_after'] for r in receipt['rounds']]])
(D/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','proofs']}))
