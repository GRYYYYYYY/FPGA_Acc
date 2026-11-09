"""Fresh unseeded comparison with identical native binary and fixed inputs."""
import sys,json,time,os,shutil,subprocess,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
from canonical_reload_identity_only_v2 import canonical_reload,binary,identity
from rr_graph import read_rr_graph
from stream_native_route_audit import audit
from audit_native_route import NET
from collections import Counter
src=R/'experiments/resident_wire_span_full_v1_2026-10-08';out=R/'experiments/resident_wire_span_fresh_cold_v1_2026-10-08';out.mkdir()
p=src/'receipt.json';data=json.loads(p.read_text());assert all(sha(k)==v for k,v in data['bindings'].items())
bindings={**closure([Path(__file__)]),str(p):sha(p),str(binary):sha(binary),str(identity):sha(identity)}
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
from shared_compact_native_inventory_v1 import Inventory
bindings.update({str(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr'):sha(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr')});rows=[]
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'order':['bigkey','dsip','misex3','frisc'],'policy':'Same seed-capable binary, same command, graph and original fixed placement; all ROUTECAST environment absent. All outcomes retained. CPD and wirelength each must not increase for quality gate. Continuous fresh endpoint conversion, copying inputs, native route, endpoint/capacity audit, original canonical reload and final output hashing; no estimator/floors/seed preparation charged to cold. Upstream pack/place/RR generation and compilation excluded. Per-case timer begins before copied-input verification.'},indent=2)+'\n')
for candidate in data['rows']:
 name=candidate['name'];begin=time.perf_counter();w=out/name;w.mkdir();row={'name':name,'status':'FAILED','stages':{}}
 try:
  assert all(sha(k)==v for k,v in candidate['files'].items())
  tick=time.perf_counter();old=json.loads((R/f'experiments/mcnc_prospective_v1_2026-10-07/{name}/endpoints.json' if name!='frisc' else R/'experiments/frisc_endpoints_2026-10-05/endpoints.json').read_text());ep,mapping=extract(*(Path(old['inputs'][k]['path']) for k in ['net','place','graph']));assert ep['connections']==old['connections'];(w/'endpoints.json').write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n');row['stages']['conversion']=time.perf_counter()-tick
  for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/name/f,w/f)
  cmd=candidate['canonical']['command'].copy();cmd[0]=str(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr');cmd[cmd.index('--analysis')]='--route';cmd[cmd.index('--route_file')+1]='output.route';bindings[cmd[0]]=sha(cmd[0]);bindings[cmd[1]]=sha(cmd[1]);graph=Path(cmd[cmd.index('--read_rr_graph')+1]);bindings[str(graph)]=sha(graph)
  tick=time.perf_counter()
  with (w/'native.log').open('w') as log:code=subprocess.run(cmd,cwd=w,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  row.update(command=cmd,native_exit_code=code,native_seconds=time.perf_counter()-tick)
  log=(w/'native.log').read_text();assert code==0 and 'NET-aware seed imported' not in log and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
  cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);row.update(cpd_ns=cpd,wirelength=wire)
  row['stages']['native']=row['native_seconds'];tick=time.perf_counter()
  a=audit(graph,w/'output.route');names={int(m[1]):m[2] for line in (w/'output.route').read_text().splitlines() if (m:=NET.match(line))}
  required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);observed=Counter((names[q['net_id']],q['source'],q['sink']) for q in a['connections'] if names[q['net_id']] in set(ep['net_names'].values()));assert required==observed and a['overflow_units']==0
  (w/'native_audit.json').write_text(json.dumps(a)+'\n')
  row['stages']['audit']=time.perf_counter()-tick;tick=time.perf_counter()
  files={str(f):sha(f) for f in w.iterdir() if f.is_file()}
  canonical=canonical_reload({**row,'width':candidate['canonical']['width'],'decision':'R','files':files},w,out/(name+'_canonical'),Inventory(graph))
  row['stages']['canonical']=time.perf_counter()-tick
  row.update(canonical=canonical,status='COLD_NATIVE_AND_CANONICAL_PASS',candidate_cpd_ns=candidate['cpd_ns'],candidate_wirelength=candidate['wirelength'],candidate_quality_gate_pass=candidate['cpd_ns']<=cpd and candidate['wirelength']<=wire)
 except Exception as error:row['error']=repr(error)
 row['files']={str(f):sha(f) for f in w.iterdir() if f.is_file()};row['actual_complete_workflow_seconds']=time.perf_counter()-begin;rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,row['status'],row.get('cpd_ns'),row.get('wirelength'),row.get('candidate_quality_gate_pass'),row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Fresh cold continuous fixed-input-to-native-audit-and-canonical workflow clock. Compare with resident_wire_span_full_v1; noninterleaved single run, no stable statistical speed claim.'},indent=2)+'\n')
assert all(r['status']=='COLD_NATIVE_AND_CANONICAL_PASS' for r in rows)
