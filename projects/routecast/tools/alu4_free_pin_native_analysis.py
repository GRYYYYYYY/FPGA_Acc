"""Isolated native VPR route import/check/analysis of frozen RouteCast paths."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/alu4_free_pin_native_analysis_2026-10-05');cwd=Path('work/alu4_free_pin_native_analysis_2026-10-05')
if out.exists() or cwd.exists():raise ValueError('fresh isolated directories required')
p=json.loads(Path('experiments/alu4_validation_capture_2026-10-05/protocol.json').read_text());inputs=p['inputs'].copy();
for key in ('net','place'):
 f=Path('work/alu4_validation_capture_2026-10-05')/f'alu4.{key}';inputs[key]={'path':str(f.resolve()),'sha256':sha(f)}
inputs['graph']={'path':str(Path('work/alu4_validation_capture_2026-10-05/rr_graph.xml').resolve()),'sha256':sha('work/alu4_validation_capture_2026-10-05/rr_graph.xml')};route=Path('experiments/alu4_free_pin_route_export_2026-10-05/alu4.route');inputs['route']={'path':str(route.resolve()),'sha256':sha(route)};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();cwd.mkdir();(out/'source.py').write_text(Path(__file__).read_text())
for key in ('blif','net','place','route'):shutil.copyfile(inputs[key]['path'],cwd/f'alu4.{key}')
command=[inputs['vpr']['path'],inputs['arch']['path'],'alu4.blif','--analysis','--net_file','alu4.net','--place_file','alu4.place','--route_file','alu4.route','--read_rr_graph',inputs['graph']['path'],'--route_chan_width','200','--num_workers','1','--seed','1','--timing_report_npaths','100','--timing_report_detail','detailed']
protocol={'inputs':inputs,'command':command,'cwd':str(cwd.resolve()),'timeout_s':120,'source_sha256':sha(out/'source.py'),'scope':'native analysis import of exact exported RouteCast RR trees; no rerouting, no native-label-driven tuning'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
with (out/'stdout.txt').open('w') as log:
 try:result=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=120);exitcode=result.returncode;timeout=False
 except subprocess.TimeoutExpired:exitcode=None;timeout=True
reports={}
for f in cwd.glob('*timing*.rpt'):shutil.copyfile(f,out/f.name);reports[f.name]=sha(out/f.name)
r={'exit_code':exitcode,'timed_out':timeout,'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'stdout_sha256':sha(out/'stdout.txt'),'input_hashes_unchanged':all(sha(v['path'])==v['sha256'] for v in inputs.values()),'copied_route_unchanged':sha(cwd/'alu4.route')==inputs['route']['sha256'],'reports':reports};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
