"""Runtime missing-NET and stale/partial seed qualification on all3 source widths."""
import json,re,os,sys,subprocess,shutil,resource
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_source_restart_boundaries_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
def main():
 D.mkdir(exist_ok=False);old=read(E/'wbuart_source_restart_loaded_qualification_v1_2026-10-20/manifest.json');qualification=E/'wbuart_source_restart_loaded_qualification_v1_2026-10-20/independent_input_verification_v1.json';assert read(qualification)['status']=='ALL3_SOURCE1074_TREES_AND2493_DELAY_MULTISETS_VERIFIED';runner=R/'tools/run_wbuart_source_restart_case_v2.py';bindings={str(p):sha(p) for p in [Path(__file__),runner,qualification]};cases=[];fixtures=[]
 for c in old['cases']:
  c=dict(c);width=c['width'];folder=D/f'w{width:03d}';folder.mkdir();seed=Path(c['restart_seed']);text=seed.read_text();parts=re.split(r'(?=^Net \d+ \()',text,flags=re.M);header=parts[0];blocks=parts[1:];assert blocks[0].startswith('Net 0 ');missing=folder/'missing_NET0.route';missing.write_text(header+''.join(blocks[1:]));partial=folder/'partial_NET0.route';first=blocks[0].splitlines(keepends=True);sink=next(i for i,l in enumerate(first) if 'SINK' in l);assert sum('SINK' in l for l in first)>1;partial.write_text(header+''.join(first[:sink+1])+'\n\n'+''.join(blocks[1:]));stale=folder/'stale_placement.route';stale.write_text(re.sub(r'Placement_ID: SHA256:[0-9a-f]+','Placement_ID: SHA256:'+'0'*64,text,count=1))
  ep=read(c['endpoint']);physical=audit(ep['inputs']['graph']['path'],missing);names={int(m[1]):m[2] for l in missing.read_text().splitlines() if (m:=NET.match(l))};expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'] if q['net_id']!=0);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in physical['connections']);assert observed==expected and physical['overflow_units']==0
  proof=folder/'seed_verification.json';proof.write_text(json.dumps({'status':'SOURCE_SUBSET_SEED_PHYSICAL_ENDPOINT_CAPACITY_PASS','removed_NETs':[0],'remaining_connections':len(observed),'bindings':{str(p):sha(p) for p in [missing,seed,Path(c['restart_seed_proof']),Path(c['endpoint'])]}},indent=2)+'\n')
  c.update(case=f'w{width:03d}/source/missing_NET0',output=str(folder/'missing_native'),restart_seed=str(missing),restart_seed_proof=str(proof),expected_load_marker='ROUTECAST_SOURCE_RESTART retained=1073 missing=1 retained_pins=2491 missing_delay=1e-9');cases.append(c)
  for mode,p,message in [('stale',stale,'does not match the loaded placement'),('partial',partial,'restart requires complete retained NET')]:fixtures.append({'width':width,'case':c['case'],'seed':str(p),'mode':mode,'expected_error':message,'command':c['command'],'inputs':c['inputs'],'output':str(folder/mode)})
  for p in [seed,missing,partial,stale,proof]:bindings[str(p)]=sha(p)
 mp=D/'manifest.json';mp.write_text(json.dumps({'schema':'WBUART_SOURCE_RESTART_QUALIFICATION_V1','phase':'source_qualification','native_execution_admitted':True,'cases':cases,'negative_fixtures':fixtures,'bindings':bindings,'scope':'Drop NET0 only on each existing source layout; missing1ns initialization and negative stale-placement/partial retained NET behavior. No target-label, quality or gain claim.'},indent=2)+'\n')
 rows=[]
 for c in cases:
  with (D/(c['case'].replace('/','_')+'.log')).open('x') as f:rc=subprocess.call([sys.executable,str(runner),str(mp),c['case']],stdout=f,stderr=subprocess.STDOUT)
  v=read(Path(c['output'])/'verification.json');assert rc==0 and v['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';log=(Path(c['output'])/'native.log').read_text();delay=re.findall(r'ROUTECAST_SOURCE_RESTART_DELAY net=0 pin=(\d+) value=(\S+)',log);assert {int(pin) for pin,value in delay}=={1,2};import struct
  value=struct.unpack('f',struct.pack('f',1e-9))[0];assert all(float.fromhex(v)==value for pin,v in delay);rows.append({'case':c['case'],'missing_NET0_delay_float32_1ns_exact':True,'physical_canonical_trace_pass':True});print(rows[-1],flush=True)
 for f in fixtures:
  out=Path(f['output']);out.mkdir()
  for k,n in [('blif','design.blif'),('net','design.net'),('place','design.place')]:shutil.copyfile(f['inputs'][k],out/n)
  env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_NATIVE_SEED=f['seed'],ROUTECAST_SOURCE_SEEDED_RESTART='1')
  with (out/'native.log').open('x') as log:rc=subprocess.run(f['command'],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limit).returncode
  log=(out/'native.log').read_text();assert rc!=0 and f['expected_error'] in log and 'VPR succeeded' not in log and 'ROUTECAST_SOURCE_RESTART retained=' not in log;rows.append({'width':f['width'],'mode':f['mode'],'exit_status':rc,'expected_rejection':True});print(rows[-1],flush=True)
 assert len(rows)==9
 (D/'verification.json').write_text(json.dumps({'status':'ALL3_MISSING_NET_INITIAL_DELAYS_AND6_NEGATIVE_SEEDS_RUNTIME_QUALIFIED','rows':rows,'bindings':{str(mp):sha(mp),**{str(p):sha(p) for p in D.rglob('native.log')}},'scope':'Source-only missing-NET and stale/partial input qualification. No missing-pin delay-bound, persistent full-state, target reference or quality/gain claim.'},indent=2)+'\n')
if __name__=='__main__':main()
