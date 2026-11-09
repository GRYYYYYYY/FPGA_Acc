"""Complete cached audit comparison on copies of immutable certified model files."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from time import perf_counter
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
from pre_route_endpoints import sha
name=sys.argv[1];assert name in ['xtea','8051','mmc']
old=R/'experiments/resident_radix_count_complete_v4_2026-10-08'/name
admission=R/'experiments/resident_radix_count_complete_v4_2026-10-08/independent_verification_v4.json'
proof=json.loads(admission.read_text());assert proof['all_three_complete_case_correctness_gates_pass']
assert all(sha(p)==h for p,h in proof['bindings'].items())
contract=R/'experiments/fraction_arc_cache_contract_v1_2026-10-08/verification.json'
c=json.loads(contract.read_text());assert c['pass_all'] and all(sha(p)==h for p,h in c['bindings'].items())
scripts=['verify_resident_demand_frame_physical_rc_cache_v4.py','verify_resident_events_fraction_cache_v5.py']
files=['protocol.json','receipt.json','initial.json','sketch.json','floors.json','round0.json','round1.json']
original_proofs=['initial_physical_verification.json','sketch_physical_verification.json','verification.json']
bindings={**closure([Path(__file__),*[R/'tools'/s for s in scripts]]),str(admission):sha(admission),str(contract):sha(contract),
          **{str(old/f):sha(old/f) for f in files+original_proofs}}
D=R/'experiments/fraction_cached_audit_complete_v1_2026-10-08'/name
D.mkdir(parents=True,exist_ok=False);out=D/'model_copy';out.mkdir()
for f in files:shutil.copyfile(old/f,out/f)
copies={str(out/f):sha(old/f) for f in files}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,copies=copies,
    scope='All original immutable state files copied byte-for-byte and checked before/after every complete audit. Original round state paths remain authenticated. Only Fraction class/switch cost calculation cached; all scientific outputs must equal original proofs excluding source bindings. Single cached audit clocks, no paired speed claim.'),indent=2)+'\n')
outputs=[out/'initial_physical_verification_rc_cache_v4.json',out/'sketch_physical_verification_rc_cache_v4.json',D/'events_cached.json']
commands=[[scripts[0],out,'initial'],[scripts[0],out,'sketch'],[scripts[1],out,name,outputs[2]]]
rows=[]
for stage,args in enumerate(commands):
    assert all(sha(p)==h for p,h in {**bindings,**copies}.items())
    tick=perf_counter()
    with (D/f'stage{stage}.log').open('w') as log:
        proc=subprocess.run([sys.executable,str(R/'tools'/args[0]),*[str(x) for x in args[1:]]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
    seconds=perf_counter()-tick
    if proc.returncode:
        (D/'failure.json').write_text(json.dumps(dict(stage=stage,exit_code=proc.returncode))+'\n')
        raise SystemExit(proc.returncode)
    cached=json.loads(outputs[stage].read_text());original=json.loads((old/original_proofs[stage]).read_text())
    for proof in [cached,original]:assert all(sha(p)==h for p,h in proof['bindings'].items())
    assert {k:v for k,v in cached.items() if k!='bindings'}=={k:v for k,v in original.items() if k!='bindings'}
    assert all(sha(p)==h for p,h in {**bindings,**copies}.items())
    rows.append(dict(stage=stage,complete_scientific_output_equal=True,seconds=seconds,
                     proof=str(outputs[stage]),sha256=sha(outputs[stage])))
    print(name,'CACHED_AUDIT_PASS',stage,seconds,flush=True)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,copies=copies,rows=rows,
    all_three_complete_scientific_outputs_equal=True),indent=2)+'\n')
