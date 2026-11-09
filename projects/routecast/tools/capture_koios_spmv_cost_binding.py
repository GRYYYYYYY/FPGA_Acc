"""Isolated existing-route analysis and native graph/cost binding export."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/koios_spmv_cost_binding_2026-10-04');work=Path('work/koios_spmv_cost_binding_2026-10-04')
if out.exists() or work.exists():raise ValueError('fresh directories required')
ready=json.loads(Path('experiments/clma_frozen_tree_pressure_2026-10-04/family_readiness.json').read_text());exe=Path('build/cost_binding_export_2026-10-04/routecast_cost_binding_export').resolve();br=json.loads((exe.parent/'receipt.json').read_text());assert br['executable_sha256']==sha(exe)
inputs={'vpr':{'path':str(exe),'sha256':sha(exe)},'arch':ready['architecture']}
for name,f in [('blif','spmv.pre-vpr.blif'),('net','spmv.net'),('place','spmv.place'),('route','spmv.route')]:inputs[name]=ready['input_files'][f]
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());out.mkdir();work.mkdir();(out/'source').mkdir()
for f in (Path(__file__),Path(__file__).with_name('pre_route_endpoints.py')):shutil.copyfile(f,out/'source'/f.name)
for name in ('blif','net','place','route'):shutil.copyfile(inputs[name]['path'],work/f'spmv.{name}')
cmd=[str(exe),inputs['arch']['path'],'spmv.blif','--analysis','--net_file','spmv.net','--place_file','spmv.place','--route_file','spmv.route','--route_chan_width','300','--num_workers','1','--seed','1','--reorder_rr_graph_nodes_algorithm','none','--write_rr_graph','rr_graph.xml','--echo_file','on']
p={'inputs':inputs,'command':cmd,'cwd':str(work.resolve()),'scope':'existing-route analysis only, no new routing; native graph export and per-node cost-index capture; not holdout predictor validation','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic()
with (out/'vpr_stdout.txt').open('w') as log:r=subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=300)
outputs={}
for name in ('rr_graph.xml','rr_indexed_data.echo','routecast_node_cost_indices.csv'):
 f=work/name
 if f.exists():shutil.copyfile(f,out/name);outputs[name]=sha(out/name)
receipt={'protocol_sha256':sha(out/'protocol.json'),'exit_code':r.returncode,'wall_s':time.monotonic()-start,'outputs':outputs,'stdout_sha256':sha(out/'vpr_stdout.txt'),'original_inputs_unchanged':all(sha(v['path'])==v['sha256'] for v in inputs.values())};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if r.returncode or len(outputs)!=3:raise SystemExit(1)
