"""Isolated evaluator-side native analysis; expose only cost-table bindings."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
root=Path('experiments/stereo_prospective_validation_2026-10-05');p=json.loads((root/'protocol.json').read_text());out=root/'native_cost_binding';work=Path('work/stereo_native_cost_binding_2026-10-05')
if out.exists() or work.exists():raise ValueError('fresh directories required')
exe=Path('build/cost_binding_export_2026-10-04/routecast_cost_binding_export').resolve();br=json.loads((exe.parent/'receipt.json').read_text());assert sha(exe)==br['executable_sha256']
origin=json.loads(Path(p['source_record']['path']).read_text());assert sha(p['source_record']['path'])==p['source_record']['sha256'];route=origin['source_inputs']['route'];assert sha(route['path'])==route['sha256']
inputs=dict(p['inputs']);inputs['vpr']={'path':str(exe),'sha256':sha(exe)};inputs['evaluator_route']=route
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();work.mkdir();shutil.copyfile(__file__,out/'driver.py')
local={}
for name in ('circuit','packed_netlist','placement','sdc','evaluator_route'):
 f=Path(inputs[name]['path']);dest=work/f.name;shutil.copyfile(f,dest);assert sha(dest)==inputs[name]['sha256'];local[name]=dest.name
command=[str(exe),inputs['architecture']['path'],local['circuit'],'--analysis','--net_file',local['packed_netlist'],'--place_file',local['placement'],'--route_file',local['evaluator_route'],'--sdc_file',local['sdc'],'--read_rr_graph',inputs['graph']['path'],'--route_chan_width','300','--num_workers','1','--seed','3','--reorder_rr_graph_nodes_algorithm','none','--echo_file','on']
protocol={'inputs':inputs,'command':command,'cwd':str(work.resolve()),'timeout_s':600,'generator_outputs_only':['rr_indexed_data.echo','routecast_node_cost_indices.csv'],'evaluator_only':['route','native timing reports','native stdout'],'scope':'existing-route analysis, no reroute or predictor; native graph costs are architectural, no native labels supplied to generator','driver_sha256':sha(out/'driver.py')};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
try:
 with (out/'stdout.log').open('w') as log:r=subprocess.run(command,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=600)
 outputs={}
 for name in protocol['generator_outputs_only']:
  f=work/name
  if f.exists():shutil.copyfile(f,out/name);outputs[name]=sha(out/name)
 receipt={'exit_code':r.returncode,'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'outputs':outputs,'shared_inputs_unchanged':all(sha(v['path'])==v['sha256'] for v in inputs.values())};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
 assert r.returncode==0 and len(outputs)==2 and receipt['shared_inputs_unchanged']
except BaseException as error:
 (out/'failure.json').write_text(json.dumps({'error':repr(error),'wall_s':time.monotonic()-start},indent=2)+'\n');raise
