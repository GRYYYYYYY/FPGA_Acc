"""Frozen three-arm native development ablation; stage timings, not full workflow."""
import json,sys,os,shutil,subprocess,time,re
from pathlib import Path
from collections import Counter
sys.path[:0]=[str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from stream_native_route_audit import audit
from audit_native_route import NET
R=Path(__file__).resolve().parents[1];P=R/'experiments/xtea_seed_selection_native_routes_v1_2026-10-09';proof=P/'receipt.json';p=json.loads(proof.read_text())
for section in ['bindings','files']:
 assert all(sha(k)==h for k,h in p[section].items())
assert len(p['rows'])==2 and all(x['status']=='IDENTITY_AND_TREE_SERIALIZATION_PASS' for x in p['rows'])
epfile=next(Path(k) for k in p['bindings'] if k.endswith('/endpoints.json'));ep=json.loads(epfile.read_text());source=Path(ep['inputs']['net']['path']).parent;graph=Path(ep['inputs']['graph']['path']);B=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';ARCH=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml'
D=R/'experiments/xtea_selection_native_ablation_v1_2026-10-09';D.mkdir();bindings={**closure([Path(__file__)]),str(proof):sha(proof),str(epfile):sha(epfile),str(B):sha(B),str(ARCH):sha(ARCH)}
for n in ['design.blif','design.net','design.place']:bindings[str(source/n)]=sha(source/n)
bindings.update({x['path']:x['sha256'] for x in ep['inputs'].values()})
cmd=[str(B),str(ARCH),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full']
order=['cold','connection_count','connection_per_channel_span'];protocol=dict(bindings=bindings,command=cmd,arm_order=order,timeout_seconds=180,scope='Frozen archived XTEA development inputs, identical native options, all native nets routed. Selection/model/serialization preparation upstream excluded; native subprocess and independent audit timings reported separately. No full-workflow, replicate, heldout, canonical admission or gain proof. Every failure retained, no retries. Original explicit endpoint scope retained; FULL checks entire route.')
(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
for arm in order:
 w=D/arm;w.mkdir();row=dict(arm=arm,status='NOT_EXECUTED')
 try:
  assert all(sha(k)==h for k,h in bindings.items())
  for n in ['design.blif','design.net','design.place']:shutil.copyfile(source/n,w/n)
  extra={}
  if arm!='cold':
   seed=w/'seed.route';shutil.copyfile(P/arm/'seed.route',seed);extra['ROUTECAST_NATIVE_SEED']=str(seed)
  tick=time.perf_counter()
  with (w/'native.log').open('w') as f:
   try:result=subprocess.run(cmd,cwd=w,env={**env,**extra},stdout=f,stderr=subprocess.STDOUT,timeout=180);code=result.returncode
   except subprocess.TimeoutExpired:code='TIMEOUT'
  row.update(exit_code=code,native_seconds=time.perf_counter()-tick);log=(w/'native.log').read_text();assert code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;assert ('NET-aware seed imported' in log)==(arm!='cold')
  tick=time.perf_counter();a=audit(graph,w/'output.route');(w/'physical_audit.json').write_text(json.dumps(a)+'\n');assert a['overflow_units']==0
  names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))};scoped={ep['net_names'][str(q['net_id'])] for q in ep['connections']};expected=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in scoped);assert observed==expected
  row.update(status='NATIVE_FULL_AND_SCOPED_PHYSICAL_PASS',audit_seconds=time.perf_counter()-tick,scoped_connections=len(ep['connections']),wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]),diagnostic_cpd_ns=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]))
 except Exception as error:row.update(status='FAILED_OR_REJECTED',error=repr(error))
 row['files']={str(f):sha(f) for f in w.iterdir() if f.is_file()};rows.append(row);(D/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(row['arm'],row['status'],row.get('error'),flush=True)
assert all(sha(k)==h for k,h in bindings.items());(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope=protocol['scope']),indent=2)+'\n')
