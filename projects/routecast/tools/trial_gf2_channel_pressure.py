"""Predeclared full-family channel-width pressure labels; retain every failure."""
import json,os,subprocess,shutil,time,re
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_channel_pressure_2026-10-06';out.mkdir();work=root/'work/gf2_channel_pressure_2026-10-06';work.mkdir();shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';binary=shared/'build_tileplace_vpr/vpr/vpr';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';cases=[]
for data_width in (32,64,128):
 source=root/f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{data_width}'
 for channels in (16,32,64):
  d=work/f'gf2_d{data_width}_w{channels}';d.mkdir()
  for n in ('design.blif','design.net','design.place'):shutil.copyfile(source/n,d/n)
  cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','design.route','--write_rr_graph','rr_graph.xml','--route_chan_width',str(channels),'--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
  cases.append({'data_width':data_width,'channels':channels,'cwd':str(d),'command':cmd,'input_sha256':{n:sha(d/n) for n in ('design.blif','design.net','design.place')}})
p={'cases':cases,'binary_sha256':sha(binary),'architecture_sha256':sha(arch),'source_sha256':sha(Path(__file__)),'timeout_s':180,'scope':'Posthoc development pressure cohort; all three correlated GF2 variants x widths16/32/64 frozen before any run. Same packed NET/physical placement, regenerated RR per channel width. Labels only; no tuned predictor validation, minimum-width claim or physical-board result. Preserve failure/timeout separately from verified success.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');rows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for case in cases:
 d=Path(case['cwd']);start=time.monotonic();timed_out=False
 with (d/'run.log').open('w') as f:
  try:code=subprocess.run(case['command'],cwd=d,stdout=f,stderr=subprocess.STDOUT,env=env,timeout=p['timeout_s']).returncode
  except subprocess.TimeoutExpired:code=None;timed_out=True
 text=(d/'run.log').read_text();success=code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text);row={'data_width':case['data_width'],'channels':case['channels'],'exit_code':code,'timed_out':timed_out,'FULL_success':success,'cpd_ns':float(cpd[1]) if cpd else None,'process_wall_s':time.monotonic()-start,'files_sha256':{str(f):sha(f) for f in d.iterdir() if f.is_file()},'failure_label':'TIMEOUT_UNRESOLVED' if timed_out else 'NATIVE_FAILURE_REQUIRES_DIAGNOSIS' if not success else None};rows.append(row);(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'all_cases_retained':len(rows)==len(cases)},indent=2)+'\n');print(case['data_width'],case['channels'],code,success,row['process_wall_s'],flush=True)
