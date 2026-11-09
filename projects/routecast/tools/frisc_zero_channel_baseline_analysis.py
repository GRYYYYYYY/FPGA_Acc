"""Isolated native VPR route import/check/analysis of frozen RouteCast paths."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/frisc_zero_channel_baseline_analysis_2026-10-05');cwd=Path('work/frisc_zero_channel_baseline_analysis_2026-10-05')
if out.exists() or cwd.exists():raise ValueError('fresh isolated directories required')
p=json.loads(Path('experiments/frisc_graph_capture_2026-10-05/protocol.json').read_text());inputs=p['inputs'].copy();inputs['graph']={'path':str(Path('work/frisc_graph_capture_2026-10-05/rr_graph.xml').resolve()),'sha256':sha('work/frisc_graph_capture_2026-10-05/rr_graph.xml')};route=Path('work/frisc_graph_capture_2026-10-05/frisc.route');inputs['route']={'path':str(route.resolve()),'sha256':sha(route)};assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();cwd.mkdir();(out/'source.py').write_text(Path(__file__).read_text())
for key in ('blif','net','place','route'):shutil.copyfile(inputs[key]['path'],cwd/f'frisc.{key}')
command=[inputs['vpr']['path'],inputs['arch']['path'],'frisc.blif','--analysis','--net_file','frisc.net','--place_file','frisc.place','--route_file','frisc.route','--read_rr_graph',inputs['graph']['path'],'--route_chan_width','200','--num_workers','1','--seed','1','--timing_report_npaths','100','--timing_report_detail','detailed']
protocol={'inputs':inputs,'command':command,'cwd':str(cwd.resolve()),'timeout_s':120,'source_sha256':sha(out/'source.py'),'scope':'native reference analysis under identical command settings to RouteCast import; no rerouting'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
with (out/'stdout.txt').open('w') as log:
 try:result=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=120);exitcode=result.returncode;timeout=False
 except subprocess.TimeoutExpired:exitcode=None;timeout=True
reports={}
for f in cwd.glob('*timing*.rpt'):shutil.copyfile(f,out/f.name);reports[f.name]=sha(out/f.name)
r={'exit_code':exitcode,'timed_out':timeout,'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'stdout_sha256':sha(out/'stdout.txt'),'input_hashes_unchanged':all(sha(v['path'])==v['sha256'] for v in inputs.values()),'copied_route_unchanged':sha(cwd/'frisc.route')==inputs['route']['sha256'],'reports':reports};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
