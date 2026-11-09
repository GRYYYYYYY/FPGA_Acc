"""Posthoc identical-setting STA of immutable baseline/candidate7 route snapshots."""
import json,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/frisc_native_sta_pair_v2_2026-10-05');work=Path('work/frisc_native_sta_pair_v2_2026-10-05');prior=Path('experiments/frisc_timing_native_labels_v2_2026-10-05')
if out.exists() or work.exists():raise ValueError('fresh isolated directories required')
out.mkdir();work.mkdir();(out/'source.py').write_text(Path(__file__).read_text());results=[]
for cid in (0,7):
 native=prior/f'candidate_{cid}';p=json.loads((native/'protocol.json').read_text());r=json.loads((native/'receipt.json').read_text());inputs={**p['inputs'],'route':r['final_route']};place=Path(r['final_route']['path']).with_suffix('.place');inputs['place']={'path':str(place),'sha256':sha(place)};assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
 output=out/f'candidate_{cid}';cwd=work/f'candidate_{cid}';output.mkdir();cwd.mkdir()
 for key in ('blif','net','place','route'):shutil.copyfile(inputs[key]['path'],cwd/f'diffeq.{key}')
 command=[inputs['vpr']['path'],inputs['arch']['path'],'diffeq.blif','--analysis','--net_file','diffeq.net','--place_file','diffeq.place','--route_file','diffeq.route','--read_rr_graph',inputs['graph']['path'],'--route_chan_width','200','--num_workers','1','--seed','1','--timing_report_npaths','100','--timing_report_detail','detailed']
 protocol={'inputs':inputs,'command':command,'cwd':str(cwd.resolve()),'source_sha256':sha(__file__),'native_prior_receipt_sha256':sha(native/'receipt.json'),'scope':'posthoc archived-route STA; no rerouting or proxy tuning'};(output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');t=time.monotonic()
 with (output/'stdout.txt').open('w') as log:process=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 reports={}
 for file in cwd.glob('*timing*.rpt'):shutil.copyfile(file,output/file.name);reports[file.name]=sha(output/file.name)
 receipt={'exit_code':process.returncode,'wall_s':time.monotonic()-t,'protocol_sha256':sha(output/'protocol.json'),'reports':reports,'stdout_sha256':sha(output/'stdout.txt'),'input_hashes_unchanged':all(sha(v['path'])==v['sha256'] for v in inputs.values())};(output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');assert process.returncode==0 and receipt['input_hashes_unchanged'] and 'report_timing.setup.rpt' in reports;results.append({'candidate_id':cid,**receipt});print(json.dumps({'candidate_id':cid,'exit_code':process.returncode,'wall_s':receipt['wall_s']}),flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'limitations':['STA report precision3 decimal ns','posthoc diagnosis, not prospective model evaluation']},indent=2)+'\n')
