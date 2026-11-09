"""Isolated additional-design RR graph generation, frozen before execution."""
import json,shutil,subprocess,time
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
out=Path('experiments/frisc_graph_capture_2026-10-05');work=Path('work/frisc_graph_capture_2026-10-05')
if out.exists() or work.exists():raise ValueError('fresh directories required')
base=json.loads(Path('experiments/native_iteration_capture_2026-10-04/protocol.json').read_text())['inputs'];old=Path('../persistroute/experiments/vpr9/baseline_runs/vpr_serial/frisc_seed1_cw200')
paths={'vpr':Path(base['vpr']['path']),'arch':Path(base['arch']['path']),'blif':Path(base['blif']['path']).with_name('frisc.blif'),'net':old/'frisc.net','place':old/'frisc.place'}
meta=ET.parse(paths['net']).getroot().attrib
assert meta['architecture_id']=='SHA256:'+sha(paths['arch']);assert meta['atom_netlist_id']=='SHA256:'+sha(paths['blif'])
out.mkdir();work.mkdir();(out/'source').mkdir()
for n in ('capture_frisc_graph.py','pre_route_endpoints.py'):shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
for n in ('blif','net','place'):shutil.copyfile(paths[n],work/f'frisc.{n}')
cmd=[str(paths['vpr'].resolve()),str(paths['arch'].resolve()),'frisc.blif','--route','--net_file','frisc.net','--place_file','frisc.place','--route_file','frisc.route','--write_rr_graph','rr_graph.xml','--route_chan_width','200','--num_workers','1','--seed','1','--max_router_iterations','50','--timing_report_npaths','100','--timing_report_detail','detailed']
p={'inputs':{k:{'path':str(v.resolve()),'sha256':sha(v)} for k,v in paths.items()},'command':cmd,'cwd':str(work.resolve()),'timeout_s':300,'scope':'additional frisc design frontend and native reference capture; same architecture, not unseen-family generalization','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');start=time.monotonic()
with (out/'vpr_stdout.txt').open('w') as log:r=subprocess.run(cmd,cwd=work,stdout=log,stderr=subprocess.STDOUT,timeout=300)
receipt={'protocol_sha256':sha(out/'protocol.json'),'exit_code':r.returncode,'wall_s':time.monotonic()-start,'input_identities_unchanged':all(sha(v['path'])==v['sha256'] for v in p['inputs'].values()),'artifacts':{f.name:{'path':str(f.resolve()),'sha256':sha(f)} for f in work.glob('*') if f.is_file()},'log_sha256':sha(out/'vpr_stdout.txt')};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='artifacts'}),flush=True)
assert r.returncode==0 and receipt['input_identities_unchanged']
