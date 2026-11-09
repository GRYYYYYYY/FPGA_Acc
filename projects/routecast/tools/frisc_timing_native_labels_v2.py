"""Evaluator-only fresh native labels, isolated from frozen predictor process."""
import json,re,subprocess,sys,time,shutil
from pathlib import Path
from pre_route_endpoints import sha,placements
out=Path('experiments/frisc_timing_native_labels_v2_2026-10-05');work=Path('work/frisc_timing_native_labels_v2_2026-10-05');decision_path=Path('experiments/frisc_bound_proxy_decision_v2_2026-10-05/decision.json')
assert decision_path.is_file()
if out.exists() or work.exists():raise ValueError('fresh output/work required')
out.mkdir();(out/'source').mkdir();work.mkdir()
for name in ('capture_routing_iterations.py',Path(__file__).name):shutil.copyfile(Path('tools')/name,out/'source'/name)
e=json.loads(Path('experiments/frisc_endpoints_2026-10-05/endpoints.json').read_text());config=json.loads(Path('experiments/frisc_graph_capture_2026-10-05/protocol.json').read_text());inputs={k:config['inputs'][k] for k in ('vpr','arch','blif','net')};inputs['graph']=e['inputs']['graph']
places={0:Path(e['inputs']['place']['path']),**{c:Path(f'experiments/frisc_timing_candidates_v2_2026-10-05/candidate_{c}.place') for c in range(1,9)}}
hashes={str(p):sha(p) for p in places.values()};hashes.update({v['path']:v['sha256'] for v in inputs.values()});assert all(sha(p)==h for p,h in hashes.items())
protocol={'inputs_sha256':hashes,'decision_sha256':sha(decision_path),'cases':list(range(9)),'source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')},'scope':'prospective evaluator-only single seed1 route-only run per case; frozen bound proxy on/off decision precedes labels; same architecture, not unseen-family','accept_rule':'strictly lower native wirelength and CPD <= fresh baseline, otherwise baseline','channel_width':200}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];start=time.monotonic()
for cid,place in places.items():
 native=out/f'candidate_{cid}';cwd=work/f'candidate_{cid}';command=[sys.executable,str((out/'source/capture_routing_iterations.py').resolve())]
 for key,entry in inputs.items():command+=['--'+key,entry['path']]
 command+=['--place',str(place.resolve()),'--work-dir',str(cwd.resolve()),'--output-dir',str(native.resolve()),'--channel-width','200'];t=time.monotonic();result=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (out/f'launcher_{cid}.log').write_text(result.stdout)
 if result.returncode:raise RuntimeError(f'native case {cid} failed: {result.returncode}')
 receipt=json.loads((native/'receipt.json').read_text());assert receipt['exit_code']==0 and receipt['input_identities_unchanged'];text=(native/'vpr_stdout.txt').read_text();assert sha(native/'vpr_stdout.txt')==receipt['log_sha256']
 assert 'Completed placement consistency check successfully.' in text and 'Completed routing consistency check successfully.' in text
 assert placements(cwd/'diffeq.place',inputs['net']['sha256'])==placements(place,inputs['net']['sha256'])
 row={'candidate_id':cid,'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1]),'iterations':len(receipt['iteration_files']),'launcher_wall_s':time.monotonic()-t,'native_receipt_sha256':sha(native/'receipt.json')};rows.append(row);(out/f'metrics_{cid}.json').write_text(json.dumps(row,indent=2)+'\n');print(json.dumps(row),flush=True)
assert all(sha(p)==h for p,h in hashes.items());assert sha(decision_path)==protocol['decision_sha256']
(out/'receipt.json').write_text(json.dumps({'rows':rows,'full_wall_s':time.monotonic()-start,'inputs_unchanged':True,'protocol_sha256':sha(out/'protocol.json'),'limitations':['one seed per candidate, no statistical runtime claim','native labels are not prediction inputs','acceptance gate is postroute protection']},indent=2)+'\n')
