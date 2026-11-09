"""Fresh synthesis of explicit pad I/O/enable experiment, retaining original failed pipeline."""
import json,hashlib,subprocess,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'briey_lowered_synthesis_v1_2026-10-09';D.mkdir(exist_ok=False);B=E/'briey_bidir_lowering_v1_2026-10-09';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();proof=json.loads((B/'verification.json').read_text())
for p,h in proof['bindings'].items():assert sha(p)==h
source=B/'design.json';(D/'input.json').write_bytes(source.read_bytes());old=json.loads((E/'vexriscv_family_flattened_inventory_v1_2026-10-09/protocol.json').read_text());yosys=Path(next(p for p in old['bindings'] if p.endswith('/bin/yosys')));assert sha(yosys)==old['bindings'][str(yosys)]
script='read_json input.json\nhierarchy -check -top Briey\nsynth -flatten -noabc\ndffunmap\ncheck -assert\nwrite_json design.json\n';(D/'synth.ys').write_text(script);command=[str(yosys),'-s','synth.ys'];paths=[Path(__file__).resolve(),source,B/'verification.json',B/'independent_port_check.json',yosys,D/'input.json',D/'synth.ys'];bindings={str(p):sha(p) for p in paths};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=180,scope='New lowered-boundary experimental synthesis, not original port-compatible circuit, four-state wrapper acceptance, route labels or heldout validation.'),indent=2)+'\n');start=time.perf_counter()
with (D/'log.txt').open('x') as log:
 try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=180).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
report=dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-start,admitted_for_prediction=False)
if code==0:
 modules=json.loads((D/'design.json').read_text())['modules'];assert len(modules)==1;m=modules['Briey'];assert all(p['direction'] in ('input','output') for p in m['ports'].values());report['cell_types']=dict(Counter(c['type'] for c in m['cells'].values()));report['inout_ports']=0;report['init_nets']=[dict(name=n,bits=v['bits'],value=v['attributes']['init']) for n,v in m['netnames'].items() if 'init' in v.get('attributes',{})]
report['files']={str(p):sha(p) for p in D.iterdir() if p.is_file()};(D/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(code,report['seconds'],flush=True)
