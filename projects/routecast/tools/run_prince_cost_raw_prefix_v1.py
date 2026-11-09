"""Reproduced query-byte prefixes;never substitute intentional stops for legal routing."""
import json,os,shutil,subprocess,resource,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from pre_route_endpoints import sha
from prince_configuration_identity_v1 import profile
from replay_prince_native_sources_v1 import sequences
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'prince_cost_advance_ablation_trial_v1_2026-10-20';D=E/'prince_cost_raw_prefix_trial_v1_2026-10-20';B=R/'build/prince_cost_raw_prefix_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def run_one(job):
 full=job['case'];base,mode=full.rsplit('/',1);d=D/full;d.mkdir(parents=True);old=S/full;oldreceipt=load(old/'receipt.json');command=job['command'].copy();command[0]=str(B/'vpr')
 for name,path in job['staging'].items():shutil.copyfile(path,d/name);assert sha(path)==sha(d/name)
 shutil.copyfile(old/'NET_mapping.tsv',d/'NET_mapping.tsv');launch,digest=profile(command,d/'design.blif');(d/'launch_configuration.json').write_text(json.dumps(launch,sort_keys=True,separators=(',',':')));graph=Path(command[command.index('--read_rr_graph')+1]);identity=d/'identity.txt';binary_sha=sha(B/'vpr');identity.write_text('\n'.join([sha(graph),sha(d/'design.net'),sha(d/'design.place'),binary_sha,'post_route_accumulated_cost_and_timing_update__pre_dynamic_BB_update_and_pres_advance',base,digest])+'\n');policy=d/'cost_policy.txt';policy.write_text('\n'.join(['COST_ADVANCE_ABLATION_V1',mode,base,binary_sha,digest])+'\n');raw=d/'raw_queries';raw.mkdir();(d/'boundary').mkdir();(d/'owners').mkdir();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_RESIDENT_CALLBACK_FILE=str(d/'callback.tsv'),ROUTECAST_LIVE_NET_MAP=str(d/'NET_mapping.tsv'),ROUTECAST_LIVE_IDENTITY=str(identity),ROUTECAST_QUERY_FILE=str(d/'queries.tsv'),ROUTECAST_COST_MODE=mode,ROUTECAST_COST_POLICY_FILE=str(policy),ROUTECAST_RAW_QUERY_DIR=str(raw),ROUTECAST_RESIDENT_BOUNDARY_DIR=str(d/'boundary'),ROUTECAST_RESIDENT_OWNERS_DIR=str(d/'owners'),ROUTECAST_PROCESS_CLOCK_FILE=str(d/'main_clock.tsv'));tick=time.perf_counter()
 with (d/'native.log').open('x') as log:
  proc=subprocess.Popen(command,cwd=d,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit);(d/'live_job.json').write_text(json.dumps(dict(pid=proc.pid,case=full),indent=2)+'\n');code=proc.wait()
 elapsed=time.perf_counter()-tick;ready=oldreceipt['ready_iteration'];stop=d/'queries.tsv.intentional_prefix_stop.tsv';intentional=ready is not None
 if intentional:assert code==0 and stop.read_text().strip().split()==['INTENTIONAL_QUERY_PREFIX_VALIDATION_NOT_ROUTING_SUCCESS',str(ready+1),str(ready)]
 else:assert code==oldreceipt['native_exit_code']==2 and not stop.exists() and sequences(d/'output.route')==sequences(old/'output.route')
 q=[list(map(int,line.split())) for line in (d/'queries.tsv').open()];oldq=[list(map(int,line.split())) for line in (old/'queries.tsv').open()];n=ready+1 if intentional else oldreceipt['iterations'];assert len(q)==n and q==oldq[:n];cb=[line.split()[:11] for line in (d/'callback.tsv').open()];oldcb=[line.split()[:11] for line in (old/'callback.tsv').open()];assert cb==oldcb[:n];events=[int(line.split()[0]) for line in (d/'callback.tsv.ready.tsv').open() if int(line.split()[4])];assert events==([ready] if ready else []);files={};totalbytes=0
 for i,calls,size,digest_text in (line.strip().split('\t') for line in (d/'queries.tsv.raw_sha.tsv').open()):
  i,calls,size=int(i),int(calls),int(size);p=raw/f'phase_{i}.bin';assert calls==q[i-1][1] and size==calls*120==p.stat().st_size;h=sha(p);assert digest_text.removeprefix('SHA256:').strip().lower()==h;files[str(p)]=h;totalbytes+=size
 for i in range(1,n+1):
  for name in [f'boundary/iteration_{i}.bin',f'boundary/boxes_{i}.bin',f'owners/owners_{i}.bin']:assert sha(d/name)==sha(old/name);files[str(d/name)]=sha(d/name)
 for p in [d/'native.log',d/'queries.tsv',d/'queries.tsv.raw_sha.tsv',d/'callback.tsv',d/'callback.tsv.ready.tsv',identity,policy,stop]:
  if p.exists():files[str(p)]=sha(p)
 result=dict(case=full,status='INTENTIONAL_PREFIX_VALIDATION_NOT_ROUTING_SUCCESS' if intentional else 'FULL_UNACTIVATED_FAILURE_REPRODUCED',native_exit_code=code,ready_iteration=ready,observed_phases=n,observed_query_calls=sum(r[1] for r in q),raw_query_bytes=totalbytes,full_study_prefix_counts_FNV_RR_BB_owners_equal=True,paid_window_seconds=elapsed,files=files);(d/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 D.mkdir(exist_ok=False);pp=S/'protocol.json';p=load(pp);design=S/'raw_query_prefix_validation_design_v1.json';bindings={str(x):sha(x) for x in [pp,design,B/'protocol.json',B/'receipt.json',B/'vpr',Path(__file__)]};(D/'protocol.json').write_text(json.dumps(dict(jobs=p['jobs'],bindings=bindings,scope='Supplementary raw word/order validation:36 reproduced prefixes,24 intentional ready+1 stops and12 full unactivated failures. No full legal outputs or predictor labels admitted from these runs. Original36 full native outcomes remain authoritative.'),indent=2)+'\n');rows=[]
 with ProcessPoolExecutor(max_workers=3) as pool:
  for mode in ['native','hold_pres','hold_acc','hold_both']:
   for future in as_completed([pool.submit(run_one,j) for j in p['jobs'] if j['mode']==mode]):
    row=future.result();rows.append(row);(D/'progress.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n');print('RAW_PREFIX_REPRODUCED',row['case'],row['observed_phases'],row['observed_query_calls'],flush=True)
 assert len(rows)==36 and all(sha(path)==h for path,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='ALL36_RAW_QUERY_PREFIX_REPRODUCTIONS_COMPLETE',rows=sorted(rows,key=lambda r:r['case']),bindings=bindings,scope='Supplementary validation,not36 additional completed route outcomes. Pairwise full-byte comparison pending.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
