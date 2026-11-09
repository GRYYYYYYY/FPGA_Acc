"""Whole frozen bitonic family, evaluator-only native labels with no retuning."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];front=ROOT/'experiments/bitonic_family_freeze_2026-10-07';out=ROOT/'experiments/bitonic_native_reference_2026-10-07';work=ROOT/'work/bitonic_native_reference_2026-10-07'
r=json.loads((front/'receipt.json').read_text());p=json.loads((front/'protocol.json').read_text());assert r['protocol_sha256']==sha(front/'protocol.json') and [x['count'] for x in r['rows']]==p['count'];assert all(sha(f)==h for row in r['rows'] for f,h in row['files'].items())
vtr=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';binary=vtr/'build_tileplace_vpr/vpr/vpr';arch=vtr/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';out.mkdir();work.mkdir(parents=True)
protocol=dict(frontend_receipt_sha256=sha(front/'receipt.json'),frontend_protocol_sha256=sha(front/'protocol.json'),source_sha256=sha(Path(__file__)),inputs={str(binary):sha(binary),str(arch):sha(arch)},cohort=p['count'],seed=1,workers=1,channel_width=128,max_router_iterations=100,timeout_per_case_s=180,scope='Fresh evaluator-only pack/place/route/RR labels for ALL frozen family variants, no outcome selection. Native labels must not feed predictor search. Fixed policy source frozen in frontend protocol. Prospective local provenance; no universal holdout claim, physical audit/hotspot metrics/acceptedloop costs pending.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for row in r['rows']:
 n=row['count'];wd=work/f'n{n}';wd.mkdir();src=front/f'n{n}/design.blif';shutil.copyfile(src,wd/'design.blif');cmd=[str(binary),str(arch),'design.blif','--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--write_rr_graph','rr_graph.xml'];start=time.perf_counter();timeout=False
 with (out/f'n{n}.log').open('w') as stream:
  try:code=subprocess.run(cmd,cwd=wd,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  except subprocess.TimeoutExpired:code=None;timeout=True
 rows.append(dict(count=n,exit_code=code,timed_out=timeout,seconds=time.perf_counter()-start,command=cmd,input_sha256=sha(src),files={str(f):sha(f) for f in wd.iterdir() if f.is_file()},log_sha256=sha(out/f'n{n}.log')))
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==len(r['rows'])),indent=2)+'\n');print(n,code,timeout,rows[-1]['seconds'],flush=True)
assert all(sha(f)==h for f,h in protocol['inputs'].items())
