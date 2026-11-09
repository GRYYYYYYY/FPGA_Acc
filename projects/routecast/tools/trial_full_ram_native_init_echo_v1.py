"""Actual native atom-netlist initialization readback without starting a second pack."""
import hashlib,json,subprocess
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_native_init_echo_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_native_ram_pack_v2_2026-10-09';p=json.loads((B/'protocol.json').read_text())
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
for path,h in p['bindings'].items():assert sha(Path(path))==h
source=B/'design.blif';(D/'design.blif').write_bytes(source.read_bytes())
command=p['command'][:3]+['--exit_before_pack','on','--echo_file','on','--num_workers','1','--route_chan_width','128','--seed','1']
bindings={str(path):sha(path) for path in [Path(__file__),B/'protocol.json',source,Path(command[0]),Path(command[1]),D/'design.blif']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=60,
    scope='Native parse/sweep echo only, exits before pack. Exact initialized latch readback; no second clustering, routed timing or physical initialization proof.'),indent=2)+'\n')
with (D/'native.log').open('x') as log:
    try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
out=dict(exit_code=code,bindings=bindings,passed=False,admitted_for_prediction=False)
if code==0:
    def latches(path):
        return Counter(tuple(line.split()[1:]) for line in path.read_text().splitlines() if line.startswith('.latch '))
    before=latches(source)
    original=latches(D/'atom_netlist.orig.echo.blif')
    cleaned=latches(D/'atom_netlist.cleaned.echo.blif')
    initialized=lambda rows:Counter({row:count for row,count in rows.items() if row[-1] in ('0','1')})
    assert initialized(before)==initialized(original)==initialized(cleaned)
    assert sum(initialized(before).values())==13
    out.update(passed=True,initialized_latches_preserved=13,source_latches=sum(before.values()),
        original_atom_latches=sum(original.values()),cleaned_atom_latches=sum(cleaned.values()))
out['files']={str(path):sha(path) for path in D.iterdir() if path.is_file()}
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(code,out['passed'])
