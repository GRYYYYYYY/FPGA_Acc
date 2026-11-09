"""Fresh development on/off trial; conservative audited estimator cost included."""
import json, subprocess, sys, time, re
from pathlib import Path
from pre_route_endpoints import sha, placements

out=Path('experiments/feedback_on_off_cost_2026-10-05')
if out.exists(): raise ValueError('fresh output required')
config=json.loads(Path('experiments/native_iteration_capture_2026-10-04/protocol.json').read_text())
inputs=config['inputs']
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir(); (out/'source').mkdir()
import shutil
for name in ('feedback_on_off_cost_trial.py','local_batch_search_prepared_maps.py','capture_routing_iterations.py'):
    shutil.copy2(Path('tools')/name,out/'source'/name)
protocol={'inputs':inputs,'candidate_rule':'minimum channel_net_span_sum, then predicted_channel_overuse_units, then candidate ID; baseline 0',
          'order':['off','estimator','on'],'channel_width':200,
          'scope':'single development design, one ordered pair; estimator includes correctness audits and archive overhead; frozen preexisting candidates exclude candidate-generation cost; no deployment or generalized speed claim',
          'source_sha256':{p.name:sha(p) for p in (out/'source').iterdir()}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
def run_native(name,place):
    command=[sys.executable,'tools/capture_routing_iterations.py']
    for key in ('vpr','arch','blif','net','graph'): command+=['--'+key,inputs[key]['path']]
    work=Path('work/feedback_on_off_cost_2026-10-05')/name
    command+=['--place',str(place),'--work-dir',str(work),'--output-dir',str(out/name),'--channel-width','200']
    start=time.monotonic()
    with (out/(name+'_launcher.log')).open('w') as log:
        status=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
    wall=time.monotonic()-start
    assert status==0
    receipt=json.loads((out/name/'receipt.json').read_text())
    assert receipt['exit_code']==0 and receipt['input_identities_unchanged']
    assert placements(work/'diffeq.place',inputs['net']['sha256'])==placements(place,inputs['net']['sha256'])
    text=(out/name/'vpr_stdout.txt').read_text()
    assert sha(out/name/'vpr_stdout.txt')==receipt['log_sha256']
    return {'launcher_wall_s':wall,'route_failure':False,
            'wirelength':int(re.search(r'Total wirelength:\s*(\d+)',text)[1]),
            'iterations':int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]),
            'cpd_ns':float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+) ns',text)[1])}
off=run_native('off',Path(inputs['place']['path']))
start=time.monotonic()
with (out/'estimator_launcher.log').open('w') as log:
    status=subprocess.run([sys.executable,'tools/local_batch_search_prepared_maps.py','--output',str(out/'estimator')],stdout=log,stderr=subprocess.STDOUT).returncode
assert status==0
estimator_s=time.monotonic()-start
receipt=json.loads((out/'estimator/receipt.json').read_text())
baseline=json.loads(Path('experiments/matched_hpwl_trial_2026-10-04/decision.json').read_text())['rows'][0]
rows=[baseline]+[{'candidate_id':r['candidate_id'],**r['scores']} for r in receipt['reports']]
selected=min(rows,key=lambda r:(r['channel_net_span_sum'],r['predicted_channel_overuse_units'],r['candidate_id']))['candidate_id']
(out/'decision.json').write_text(json.dumps({'selected':selected,'rule':protocol['candidate_rule']},indent=2)+'\n')
place=Path(inputs['place']['path']) if selected==0 else Path(f'experiments/matched_hpwl_trial_2026-10-04/candidate_{selected}.place')
on=run_native('on',place)
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
result={'protocol_sha256':sha(out/'protocol.json'),'off':off,'on':on,'selected':selected,
        'full_estimator_launcher_s':estimator_s,'on_accounted_total_s':estimator_s+on['launcher_wall_s'],
        'off_accounted_total_s':off['launcher_wall_s'],'scope':protocol['scope']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
