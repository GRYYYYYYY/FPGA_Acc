"""Read-only baseline route STA in isolated work/output directories."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha

out=Path('experiments/clma_cost_binding_2026-10-04');work=Path('work/clma_cost_binding_2026-10-04')
if out.exists() or work.exists():raise ValueError('fresh directories required')
baseline=json.loads(Path('experiments/native_iteration_capture_2026-10-04/protocol.json').read_text())['inputs']
front=json.loads(Path('experiments/clma_constant_policy_2026-10-04/protocol.json').read_text())['inputs']
route=Path('../persistroute/experiments/vpr9/clma_seed1/clma.route')
inputs={'vpr':baseline['vpr'],'arch':baseline['arch'],'blif':front['atom'],'net':front['net'],'place':front['place'],'graph':front['graph'],'route':{'path':str(route.resolve()),'sha256':sha(route)}}
executable=Path('build/cost_binding_export_2026-10-04/routecast_cost_binding_export').resolve();build_receipt=json.loads((executable.parent/'receipt.json').read_text());assert build_receipt['executable_sha256']==sha(executable);inputs['vpr']={'path':str(executable),'sha256':sha(executable)}
for e in inputs.values():
    if sha(e['path'])!=e['sha256']:raise ValueError('baseline input changed')
out.mkdir();work.mkdir();(out/'source').mkdir();shutil.copyfile(__file__,out/'source'/Path(__file__).name);shutil.copyfile(Path(__file__).with_name('pre_route_endpoints.py'),out/'source/pre_route_endpoints.py')
for name in ('blif','net','place','route'):shutil.copyfile(inputs[name]['path'],work/f'clma.{name}')
command=[inputs['vpr']['path'],inputs['arch']['path'],'clma.blif','--analysis','--reorder_rr_graph_nodes_algorithm','none','--echo_file','on','--net_file','clma.net','--place_file','clma.place','--route_file','clma.route','--read_rr_graph',inputs['graph']['path'],'--route_chan_width','200','--num_workers','1','--seed','1','--timing_report_npaths','100','--timing_report_detail','detailed']
protocol={'inputs':inputs,'command':command,'cwd':str(work.resolve()),'scope':'read-only clma native per-node cost-index export; graph node reordering disabled, no new routing','report_paths':100,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
with (out/'vpr_stdout.txt').open('w') as log:process=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=120)
reports={}
for f in list(work.glob('*timing*.rpt'))+list(work.glob('timing_graph*.echo'))+list(work.glob('rr_indexed_data.echo'))+list(work.glob('routecast_node_cost_indices.csv')):
    shutil.copyfile(f,out/f.name);reports[f.name]=sha(out/f.name)
receipt={'protocol_sha256':sha(out/'protocol.json'),'exit_code':process.returncode,'wall_s':time.monotonic()-start,'reports':reports,'stdout_sha256':sha(out/'vpr_stdout.txt'),'input_hashes_unchanged':all(sha(e['path'])==e['sha256'] for e in inputs.values())}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if process.returncode or 'report_timing.setup.rpt' not in reports:raise SystemExit(1)
