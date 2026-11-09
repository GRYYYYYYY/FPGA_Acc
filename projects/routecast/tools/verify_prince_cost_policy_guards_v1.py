"""Real native wrong-mode/foreign-policy rejection witnesses, isolated outputs."""
import json,subprocess,shutil,os,resource
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_cost_advance_ablation_trial_v1_2026-10-20';D=E/'prince_cost_policy_guards_v1_2026-10-20'
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 D.mkdir(exist_ok=False);p=json.loads((S/'protocol.json').read_text());job=next(j for j in p['jobs'] if j['case']=='w128/episode_01/native');source=Path(job['directory']);rows=[]
 for name in ['unknown_mode','mode_payload_mismatch','foreign_case','foreign_binary','foreign_launcher']:
  d=D/name;d.mkdir()
  for f in ['design.blif','design.net','design.place','NET_mapping.tsv','identity.txt','cost_policy.txt']:shutil.copyfile(source/f,d/f)
  lines=(d/'cost_policy.txt').read_text().splitlines();mode='native';expected='cost policy identity mismatch'
  if name=='unknown_mode':mode='invalid';expected='unknown cost policy'
  elif name=='mode_payload_mismatch':mode='hold_acc'
  elif name=='foreign_case':lines[2]='w128/foreign_episode'
  elif name=='foreign_binary':lines[3]='0'*64
  else:lines[4]='0'*64
  (d/'cost_policy.txt').write_text('\n'.join(lines)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESIDENT_CALLBACK_FILE=str(d/'callback.tsv'),ROUTECAST_LIVE_NET_MAP=str(d/'NET_mapping.tsv'),ROUTECAST_LIVE_IDENTITY=str(d/'identity.txt'),ROUTECAST_PROCESS_CLOCK_FILE=str(d/'main_clock.tsv'),ROUTECAST_QUERY_FILE=str(d/'queries.tsv'),ROUTECAST_COST_MODE=mode,ROUTECAST_COST_POLICY_FILE=str(d/'cost_policy.txt'));(d/'boundary').mkdir();(d/'owners').mkdir();env['ROUTECAST_RESIDENT_BOUNDARY_DIR']=str(d/'boundary');env['ROUTECAST_RESIDENT_OWNERS_DIR']=str(d/'owners')
  with (d/'native.log').open('x') as log:code=subprocess.call(job['command'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit)
  assert code!=0 and expected in (d/'native.log').read_text();rows.append(dict(guard=name,native_exit_code=code,reason=expected,files={str(q):sha(q) for q in [d/'cost_policy.txt',d/'identity.txt',d/'native.log']}));print('NATIVE_COST_POLICY_GUARD_PASS',name,code,flush=True)
 with (D/'verification.json').open('x') as f:json.dump(dict(status='ALL5_REAL_NATIVE_POLICY_IDENTITY_GUARDS_REJECT',rows=rows,bindings={str(q):sha(q) for q in [S/'protocol.json',Path(__file__),Path(job['command'][0])]},scope='Intentional early native abort witnesses,not study routes or failed scientific treatment cases;core dumps disabled.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
