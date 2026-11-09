"""Read-only baseline route STA in isolated work/output directories."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha

out=Path('experiments/elliptic_cluster_criticality_v7_2026-10-04');work=Path('work/elliptic_cluster_criticality_v7_2026-10-04')
if out.exists() or work.exists():raise ValueError('fresh directories required')
prior=Path('experiments/elliptic_graph_capture_2026-10-04');p=json.loads((prior/'protocol.json').read_text());r=json.loads((prior/'receipt.json').read_text());inputs={**p['inputs'],'route':r['artifacts']['elliptic.route'],'graph':r['artifacts']['rr_graph.xml']}
inputs['vpr']={'path':str(Path('build/timing_export_v7_2026-10-04/routecast_timing_export').resolve()),'sha256':sha('build/timing_export_v7_2026-10-04/routecast_timing_export')}
for e in inputs.values():
    if sha(e['path'])!=e['sha256']:raise ValueError('baseline input changed')
out.mkdir();work.mkdir();(out/'source').mkdir();shutil.copyfile(__file__,out/'source'/Path(__file__).name);shutil.copyfile(Path(__file__).with_name('pre_route_endpoints.py'),out/'source/pre_route_endpoints.py')
for name in ('blif','net','place','route'):shutil.copyfile(inputs[name]['path'],work/f'elliptic.{name}')
command=[inputs['vpr']['path'],inputs['arch']['path'],'elliptic.blif','--analysis','--net_file','elliptic.net','--place_file','elliptic.place','--route_file','elliptic.route','--read_rr_graph',inputs['graph']['path'],'--route_chan_width','200','--num_workers','1','--seed','1','--timing_report_npaths','100','--timing_report_detail','detailed']
protocol={'inputs':inputs,'command':command,'cwd':str(work.resolve()),'scope':'baseline existing route clustered sink criticality and atom/Tatum identity export, no candidate labels; baseline-route-derived context only','report_paths':100,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
with (out/'vpr_stdout.txt').open('w') as log:process=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=120)
reports={}
for f in list(work.glob('*timing*.rpt'))+list(work.glob('routecast_*.jsonl')):
    shutil.copyfile(f,out/f.name);reports[f.name]=sha(out/f.name)
receipt={'protocol_sha256':sha(out/'protocol.json'),'exit_code':process.returncode,'wall_s':time.monotonic()-start,'reports':reports,'stdout_sha256':sha(out/'vpr_stdout.txt'),'input_hashes_unchanged':all(sha(e['path'])==e['sha256'] for e in inputs.values())}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if process.returncode or 'report_timing.setup.rpt' not in reports:raise SystemExit(1)
