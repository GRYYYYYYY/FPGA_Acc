"""Predeclared complete fixed-placement width controls; retain every outcome."""
import hashlib,json,os,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'full_ram_width_matrix_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_route_predictor_off_v1_2026-10-09'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text());assert r['exit_code']==2
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
p=json.loads((B/'protocol.json').read_text())
commands=[];paths=[Path(__file__),B/'receipt.json',B/'protocol.json',Path(p['command'][0]),Path(p['command'][1])]
for width in (192,256):
    folder=D/f'cw{width}';folder.mkdir()
    for name in ('design.blif','design.net','design.place','development.sdc'):
        shutil.copyfile(B/name,folder/name);paths.append(folder/name)
    command=p['command'].copy();command[command.index('--route_chan_width')+1]=str(width)
    commands.append(dict(width=width,command=command,cwd=str(folder)))
bindings={str(path):sha(path) for path in paths}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=commands,timeout_each_s=600,
    baseline_width128_receipt=str(B/'receipt.json'),scope='Freeze both widths192/256 before any run; identical Full BLIF/packed input/fixed placement/20ns development SDC, seed1/workers1, failure predictor off, default max50 iterations. Do not stop after first success or infer minimum width. Engineering candidate labels only; not full functional/physical initialization proof, unseen family or net-benefit.'),indent=2)+'\n')
results=[]
for case in commands:
    folder=Path(case['cwd']);t=time.perf_counter()
    with (folder/'route.log').open('x') as log:
        try:code=subprocess.run(case['command'],cwd=folder,env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')},stdout=log,stderr=subprocess.STDOUT,timeout=600).returncode
        except subprocess.TimeoutExpired:code='TIMEOUT'
    row=dict(width=case['width'],exit_code=code,seconds=time.perf_counter()-t,route_exists=(folder/'design.route').exists(),
        bindings=bindings,admitted_for_prediction=False,files={str(path):sha(path) for path in folder.iterdir() if path.is_file()})
    (folder/'receipt.json').write_text(json.dumps(row,indent=2)+'\n')
    results.append({k:row[k] for k in ('width','exit_code','seconds','route_exists')})
    (D/'progress.json').write_text(json.dumps(results,indent=2)+'\n');print(results[-1],flush=True)
assert all(sha(path)==h for path,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,admitted_for_prediction=False,
    files={str(path):sha(path) for path in D.rglob('*') if path.is_file()}),indent=2)+'\n')
