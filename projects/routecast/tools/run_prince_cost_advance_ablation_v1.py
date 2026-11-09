"""All9 x4 preset causal arms,full native control wave before interventions."""
import json,subprocess,shutil,resource,time,os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from pre_route_endpoints import sha
from prince_configuration_identity_v1 import profile
from run_prince_native_trajectory_v1 import table
from replay_prince_native_sources_v1 import sequences
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_cost_advance_ablation_trial_v1_2026-10-20';B=R/'build/prince_cost_advance_ablation_v1_2026-10-20';OLD=E/'prince_ownership_ledger_trial_v2_2026-10-20'
def limit():
 resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def run_one(j):
 tick=time.perf_counter();d=Path(j['directory']);d.mkdir(parents=True);base=j['case'].rsplit('/',1)[0];mode=j['mode']
 for name,path in j['staging'].items():shutil.copyfile(path,d/name);assert sha(path)==sha(d/name)
 mapping=json.loads((E/'prince_resident_consumer_v1_2026-10-20'/base/'NET_mapping.json').read_text());mp=d/'NET_mapping.tsv';mp.write_text(''.join(f"{x['native_NET_id']}\t{x['endpoint_NET_id']}\t{int(x['ignored_global'])}\t{x['name']}\n" for x in sorted(mapping,key=lambda x:x['native_NET_id'])));payload,digest=profile(j['command'],d/'design.blif');(d/'launch_configuration.json').write_text(json.dumps(payload,sort_keys=True,separators=(',',':')));graph=Path(j['command'][j['command'].index('--read_rr_graph')+1]);binary_sha=sha(B/'vpr');identity=d/'identity.txt';identity.write_text('\n'.join([sha(graph),sha(d/'design.net'),sha(d/'design.place'),binary_sha,'post_route_accumulated_cost_and_timing_update__pre_dynamic_BB_update_and_pres_advance',base,digest])+'\n');policy=d/'cost_policy.txt';policy.write_text('\n'.join(['COST_ADVANCE_ABLATION_V1',mode,base,binary_sha,digest])+'\n');(d/'policy_mode.json').write_text(json.dumps(dict(mode=mode,case=base,binary_sha256=binary_sha,launcher_digest=digest,policy_sha256=sha(policy),policy_binding='Mode separate from unchanged native router-option digest;native loader verifies joint policy/native identity.'),indent=2)+'\n')
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESIDENT_CALLBACK_FILE=str(d/'callback.tsv'),ROUTECAST_LIVE_NET_MAP=str(mp),ROUTECAST_LIVE_IDENTITY=str(identity),ROUTECAST_PROCESS_CLOCK_FILE=str(d/'main_clock.tsv'),ROUTECAST_QUERY_FILE=str(d/'queries.tsv'),ROUTECAST_COST_MODE=mode,ROUTECAST_COST_POLICY_FILE=str(policy));(d/'boundary').mkdir();(d/'owners').mkdir();env['ROUTECAST_RESIDENT_BOUNDARY_DIR']=str(d/'boundary');env['ROUTECAST_RESIDENT_OWNERS_DIR']=str(d/'owners');nt=time.perf_counter()
 with (d/'native.log').open('x') as log:
  proc=subprocess.Popen(j['command'],cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit);(d/'live_job.json').write_text(json.dumps(dict(pid=proc.pid,case=j['case'],started_monotonic_ns=time.monotonic_ns()),indent=2)+'\n');code=proc.wait()
 text=(d/'native.log').read_text();a=table(d/'native.log');src=OLD/base/'capture';old=table(src/'native.log');cb=(d/'callback.tsv').read_text().splitlines();events=[int(x.split()[0]) for x in (d/'callback.tsv.ready.tsv').read_text().splitlines() if int(x.split()[4])];assert len(events)<=1;row=dict(case=j['case'],mode=mode,native_exit_code=code,native_full_check_pass=code==0 and 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text,iterations=len(a),ready_iteration=events[0] if events else None,callback_sequence_complete=[int(x.split()[0]) for x in cb]==list(range(1,len(a)+1)),nonclock_iteration_summaries_equal=[x[:1]+x[2:] for x in a]==[x[:1]+x[2:] for x in old],terminal_physical_sequences_equal=sequences(d/'output.route')==sequences(src/'output.route'),native_seconds=time.perf_counter()-nt,paid_case_seconds=time.perf_counter()-tick)
 if mode=='native' or not events:
  assert row['callback_sequence_complete'] and row['nonclock_iteration_summaries_equal'] and row['terminal_physical_sequences_equal']
  for name in ['queries.tsv','queries.tsv.connections.tsv','queries.tsv.ledger.bin',*[str(p.relative_to(d)) for p in (d/'boundary').glob('*.bin')],*[str(p.relative_to(d)) for p in (d/'owners').glob('*.bin')]]:assert sha(d/name)==sha(src/name),(j['case'],name)
 row['files']={str(p):sha(p) for p in [*sorted(d.glob('queries.tsv*')),d/'native.log',d/'output.route',d/'callback.tsv',d/'callback.tsv.view.tsv',d/'callback.tsv.owners.tsv',*sorted(d.glob('callback.tsv.ready*')),d/'callback.tsv.resolved.tsv',d/'callback.tsv.resolved.sha256',*sorted((d/'boundary').glob('*')),*sorted((d/'owners').glob('*')),mp,identity,d/'main_clock.tsv',policy,d/'policy_mode.json',d/'launch_configuration.json',d/'design.net',d/'design.place'] if p.exists()};(d/'receipt.json').write_text(json.dumps(row,indent=2)+'\n');(d/'terminal_job.json').write_text(json.dumps(dict(pid=proc.pid,exit_code=code),indent=2)+'\n');return row

def main():
 D.mkdir(exist_ok=False);pp=E/'prince_native_trajectory_design_v1_2026-10-20/protocol.json';p=json.loads(pp.read_text());br=json.loads((B/'receipt.json').read_text());assert sha(B/'vpr')==br['binary_sha256'];jobs=[]
 for mode in ['native','hold_pres','hold_acc','hold_both']:
  for old in p['jobs']:
   j=dict(old,mode=mode,case=old['case']+'/'+mode);j['directory']=str(D/j['case']);cmd=old['command'].copy();cmd[0]=str(B/'vpr');i=cmd.index('--save_routing_per_iteration');del cmd[i:i+2];j['command']=cmd;jobs.append(j)
 design=E/'prince_attempt_scope_competition_v1_2026-10-20/post_ready_cost_advance_ablation_design_v1.json';bindings={**p['bindings'],**{str(x):sha(x) for x in [pp,B/'receipt.json',B/'protocol.json',B/'vpr',design,Path(__file__)]}};(D/'protocol.json').write_text(json.dumps(dict(jobs=jobs,bindings=bindings,policy='Frozen all9x4 post-ready causal ablation,no learned predictor. Three process workers,8GiB child address-space limit. Entire native control wave must complete exact parity before submitting27 interventions. All failed/unactivated runs retained;runtime/reads paid,not fullpaid utility claim.'),indent=2)+'\n');rows=[];start=time.perf_counter()
 with ProcessPoolExecutor(max_workers=3) as pool:
  for wave,selected in [('native_controls',jobs[:9]),('preset_interventions',jobs[9:])]:
   (D/(wave+'_submitted.json')).write_text(json.dumps(dict(cases=[j['case'] for j in selected],submitted_monotonic_ns=time.monotonic_ns()),indent=2)+'\n');futures=[pool.submit(run_one,j) for j in selected]
   for future in as_completed(futures):
    row=future.result();rows.append(row);tmp=D/'progress.json.tmp';tmp.write_text(json.dumps(dict(rows=rows,wave=wave),indent=2)+'\n');os.replace(tmp,D/'progress.json');print('COST_ADVANCE_ARM',row['case'],row['native_exit_code'],row['iterations'],row['ready_iteration'],flush=True)
   if wave=='native_controls':assert len(rows)==9 and all(r['nonclock_iteration_summaries_equal'] and r['terminal_physical_sequences_equal'] for r in rows)
 assert len(rows)==36 and all(sha(path)==h for path,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(rows=sorted(rows,key=lambda x:x['case']),bindings={str(D/'protocol.json'):sha(D/'protocol.json'),str(Path(__file__)):sha(__file__)},continuous_seconds=time.perf_counter()-start,scope='Causal policy diagnostic. Intervened final routes are not replacement default-policy forecast labels;no original full9/native/fullpaid/unseen promotion.'),indent=2)+'\n')
if __name__=='__main__':main()
