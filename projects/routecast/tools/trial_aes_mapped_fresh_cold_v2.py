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
src=R/'experiments/aes_mapped_full_workflow_v1_2026-10-08';out=R/'experiments/aes_mapped_fresh_cold_v2_2026-10-08';out.mkdir()
p=src/'receipt.json';data=json.loads(p.read_text());assert all(sha(k)==v for k,v in data['bindings'].items())
bindings={**closure([Path(__file__)]),str(p):sha(p),str(binary):sha(binary),str(identity):sha(identity)}
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
from shared_compact_native_inventory_v1 import Inventory
bindings.update({str(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr'):sha(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr')});rows=[]
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'order':['aes_cipher','aes_inv_cipher'],'policy':'Same seed-capable binary, same command, graph and original fixed placement; all ROUTECAST environment absent. All outcomes retained. CPD and wirelength each must not increase for quality gate. Continuous fresh endpoint conversion, copying inputs, native route, endpoint/capacity audit, original canonical reload and final output hashing; no estimator/floors/seed preparation charged to cold. Upstream pack/place/RR generation and compilation excluded. Per-case timer begins before copied-input verification.'},indent=2)+'\n')
for candidate in data['rows']:
 name=candidate['name'];begin=time.perf_counter();w=out/name;w.mkdir();row={'name':name,'status':'FAILED','stages':{}}
 try:
  assert all(sha(k)==v for k,v in candidate['files'].items())
  tick=time.perf_counter();old=json.loads((R/f'experiments/aes_rr_graph_only_v1_2026-10-08/{name}/endpoints.json').read_text());ep,mapping=extract(*(Path(old['inputs'][k]['path']) for k in ['net','place','graph']));assert ep['connections']==old['connections'];(w/'endpoints.json').write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n');row['stages']['conversion']=time.perf_counter()-tick
  for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/name/f,w/f)
  shared=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
  arch=shared/'vtr_flow/arch/COFFE_22nm/k6FracN10LB_mem20K_complexDSP_customSB_22nm.xml';graph=R/f'experiments/aes_rr_graph_only_v1_2026-10-08/{name}/rr_graph.xml'
  cmd=[str(R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr'),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--seed','1','--max_router_iterations','100','--check_route','full'];bindings[cmd[0]]=sha(cmd[0]);bindings[str(arch)]=sha(arch);bindings[str(graph)]=sha(graph)
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
  canonical=canonical_reload({**row,'width':128,'decision':'R','files':files},w,out/(name+'_canonical'),Inventory(graph))
  row['stages']['canonical']=time.perf_counter()-tick
  row.update(canonical=canonical,status='COLD_NATIVE_AND_CANONICAL_PASS',candidate_status=candidate['status'],candidate_quality_gate_pass=None)
 except Exception as error:row['error']=repr(error)
 row['files']={str(f):sha(f) for f in w.iterdir() if f.is_file()};row['actual_complete_workflow_seconds']=time.perf_counter()-begin;rows.append(row);(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,row['status'],row.get('cpd_ns'),row.get('wirelength'),row.get('candidate_quality_gate_pass'),row.get('error'),flush=True)
assert all(sha(k)==v for k,v in bindings.items())
(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Fresh cold continuous fixed-input-to-native-audit-and-canonical workflow clock. Seeded AES candidates failed; no quality or speed comparison accepted; noninterleaved single run, no stable statistical speed claim.'},indent=2)+'\n')
assert all(r['status']=='COLD_NATIVE_AND_CANONICAL_PASS' for r in rows)
