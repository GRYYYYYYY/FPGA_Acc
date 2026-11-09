"""Posthoc native controls: each accepted net alone, same legal starting route."""
import json,re,time,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/frisc_trunk_batch_native_ablation_2026-10-05');work=Path('work/frisc_trunk_batch_native_ablation_2026-10-05')
if out.exists() or work.exists():raise ValueError('fresh isolated directories required')
files={'before':'experiments/frisc_shared_trunk_route_export_2026-10-05/frisc.route','after':'experiments/frisc_trunk_batch_route_export_2026-10-05/frisc.route','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json','batch_receipt':'experiments/frisc_shared_trunk_target_batch_2026-10-05/receipt.json','native_protocol':'experiments/frisc_trunk_batch_native_analysis_2026-10-05/protocol.json'};identities={p:sha(p) for p in files.values()};names=json.loads(Path(files['endpoints']).read_text())['net_names'];batch=json.loads(Path(files['batch_receipt']).read_text());selected=[r['net'] for r in batch['reports'] if r['committed']];assert selected==[49,100];protocol=json.loads(Path(files['native_protocol']).read_text());inputs={k:v for k,v in protocol['inputs'].items() if k!='route'};assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
def sections(path):
 parts=re.split(r'(?m)(?=^Net \d+ )',Path(path).read_text());chunks={}
 for chunk in parts[1:]:
  name=re.match(r'Net \d+ \((.*)\)',chunk.splitlines()[0])[1];assert name not in chunks;chunks[name]=chunk
 return parts[0],chunks
header,old=sections(files['before']);after_header,new=sections(files['after']);assert header==after_header and old.keys()==new.keys();changed={name for name in old if old[name]!=new[name]};assert changed=={names[str(n)] for n in selected};out.mkdir();work.mkdir();(out/'source.py').write_text(Path(__file__).read_text());results=[]
for net in selected:
 root=out/f'net_{net}';cwd=work/f'net_{net}';root.mkdir();cwd.mkdir();name=names[str(net)];render=header+''.join(new[n] if n==name else chunk for n,chunk in old.items());(cwd/'frisc.route').write_text(render);routehash=sha(cwd/'frisc.route')
 for key in ('blif','net','place'):shutil.copyfile(inputs[key]['path'],cwd/f'frisc.{key}')
 p={'inputs':inputs,'constructed_route_sha256':routehash,'only_replaced_frontend_net_id':net,'only_replaced_native_net_name':name,'command':protocol['command'],'cwd':str(cwd.resolve()),'source_sha256':sha(out/'source.py'),'input_sha256':identities,'scope':'posthoc per-net native ablation; other route sections byte unchanged, no model tuning or prospective selection claim'};(root/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');t=time.monotonic()
 with (root/'stdout.txt').open('w') as log:r=subprocess.run(p['command'],cwd=cwd,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 text=(root/'stdout.txt').read_text();passed=r.returncode==0 and 'Completed routing consistency check successfully.' in text and 'RouterOpts.check_route: FULL' in text and 'VPR succeeded' in text and 'analysis results are for an illegal' not in text;reports={}
 for f in cwd.glob('*timing*.rpt'):shutil.copyfile(f,root/f.name);reports[f.name]=sha(root/f.name)
 receipt={'net':net,'net_name':name,'exit_code':r.returncode,'native_full_check_passed':passed,'route_unchanged':sha(cwd/'frisc.route')==routehash,'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]) if passed else None,'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1]) if passed else None,'wall_s':time.monotonic()-t,'protocol_sha256':sha(root/'protocol.json'),'stdout_sha256':sha(root/'stdout.txt'),'reports':reports};(root/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');assert passed and receipt['route_unchanged'];results.append(receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='reports'}),flush=True)
assert all(sha(p)==h for p,h in identities.items()) and all(sha(v['path'])==v['sha256'] for v in inputs.values());(out/'receipt.json').write_text(json.dumps({'results':results,'input_sha256':identities,'source_sha256':sha(out/'source.py'),'scope':'per-net posthoc native controls; CPD interaction and pre-route prediction still require separate evidence'},indent=2)+'\n')
