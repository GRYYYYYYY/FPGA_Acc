"""Fresh fixed-target cold route cohort; all failures retained."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/bitonic_resident_live_staging_2026-10-07'
out=ROOT/'experiments/bitonic_baseline_swapped_cold_2026-10-07';out.mkdir()
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
binary=shared/'build_tileplace_vpr/vpr/vpr';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
p=json.loads((parent/'protocol.json').read_text())
inputs={str(f):sha(f) for f in [binary,arch,Path(__file__),parent/'protocol.json']}
for case in p['cases']:
 for f,d in case['bindings'].items():assert sha(f)==d;inputs[f]=d
protocol=dict(inputs=inputs,cohort=[4,8,16],seed=1,workers=1,width=128,max_iterations=100,timeout_seconds=180,scope='Fresh cold route-only on exactly staged target placement and original packed netlist/RR graph; all cases retained. Prepared input routing clock, not full accepted workflow or stable performance.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for case in p['cases']:
 n=case['count'];work=out/f'n{n}';work.mkdir();src=Path(case['source'])
 for name in ['design.blif','design.net']:shutil.copyfile(src/name,work/name)
 shutil.copyfile(parent/f'n{n}/swapped.place',work/'design.place')
 cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',str(src/'rr_graph.xml'),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
 tick=time.perf_counter();timeout=False
 with (work/'cold.log').open('w') as stream:
  try:code=subprocess.run(cmd,cwd=work,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
  except subprocess.TimeoutExpired:code=None;timeout=True
 text=(work/'cold.log').read_text();row=dict(count=n,exit_code=code,timed_out=timeout,seconds=time.perf_counter()-tick,command=cmd,files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
 if code==0:
  assert 'VPR succeeded' in text
  row.update(cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]),rrr_iterations=int(re.findall(r'Successfully routed after (\d+) routing iterations',text)[-1]))
 rows.append(row);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==3),indent=2)+'\n');print(row['count'],code,row.get('cpd_ns'),row.get('wirelength'),flush=True)
assert all(sha(f)==d for f,d in inputs.items())
