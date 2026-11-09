"""Fresh source-bound native observation of the private diagnostic route."""
import csv,hashlib,json,os,shutil,subprocess
from pathlib import Path

D=Path('work/native_joint_budget_ex5p_baseline_target_probe_20261016').resolve()
qualityfile=D/'native_validation/validation.json';q=json.loads(qualityfile.read_text())
protocol=Path('work/native_joint_budget_net_repair_v2_20261016/protocol.json');case=json.loads(protocol.read_text())['cases'][0]
O=D/'fresh_observation';O.mkdir(exist_ok=False)
for name in ['circuit.net','circuit.place','native.route']:shutil.copy2(D/'native_validation'/name,O/name)
tasks=list(csv.DictReader(open(case['connections'])))
with (O/'observation.input.csv').open('x') as stream:
    w=csv.writer(stream);w.writerow(['iteration','task_id','net_id','source','sink','routed','delay_ps','criticality_q'])
    for t in tasks:w.writerow([0,t['id'],t['net_id'],t['source'],t['sink'],0,0,0])
env={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))}
env.update(PERSISTROUTE_VPR_TIMING_INPUT=str(O/'observation.input.csv'),PERSISTROUTE_VPR_TIMING_OUTPUT=str(O/'observation.output.csv'))
inputs=[qualityfile,protocol,Path(case['connections']),Path(__file__),O/'observation.input.csv',*[O/n for n in ['circuit.net','circuit.place','native.route']]]
(O/'launch.json').write_text(json.dumps(dict(command=q['command'],cwd=str(O),source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}),indent=2)+'\n')
with (O/'analysis.stdout').open('x') as stdout,(O/'analysis.stderr').open('x') as stderr:
    rc=subprocess.run(q['command'],cwd=O,env=env,stdout=stdout,stderr=stderr).returncode
assert rc==0
obs=list(csv.DictReader((O/'observation.output.csv').open()));assert {r['task_id'] for r in obs}=={t['id'] for t in tasks}
assert (O/'report_timing.setup.rpt').read_bytes()==(D/'native_validation/report_timing.setup.rpt').read_bytes()
(O/'result.json').write_text(json.dumps(dict(status='fresh_native_observation_complete_setup_report_byte_reproduced',returncode=rc,observations=len(obs),observation_sha256=hashlib.sha256((O/'observation.output.csv').read_bytes()).hexdigest(),research_complete=False),indent=2)+'\n')
print('Fresh observation complete:',len(obs))
