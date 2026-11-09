"""First SHA160 cold labels after frozen complete predictions and audits."""
import json,sys,subprocess,shutil,os,time,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];assert name=='sha1';prp=R/'experiments/sha1_frozen_model_v1_2026-10-10/protocol.json';pr=json.loads(prp.read_text());assert all(sha(k)==h for k,h in pr['bindings'].items())
outer=R/'experiments/sha1_frozen_model_v1_2026-10-10/verification.json';v=json.loads(outer.read_text());assert v['complete_candidate_physical_and_events_pass'] and v['completed']==6273 and all(sha(k)==h for k,h in v['bindings'].items())
resident=outer.parent/name;proofs=[outer,resident/'initial_physical_verification.json',resident/'sketch_physical_verification.json',resident/'verification.json',outer.parent/'metric_rule_addendum.json']
for p in proofs:
 d=json.loads(p.read_text());assert all(sha(k)==h for k,h in d['bindings'].items())
params=dict(order=['cold','seed'],route_chan_width=pr['native']['width'],num_workers=pr['native']['workers'],seed=pr['native']['seed'],max_router_iterations=pr['native']['max_iterations'],timeout_per_case_seconds=1200)
assert params['route_chan_width']==128 and params['seed']==params['num_workers']==1 and params['max_router_iterations']==100
src=R/'experiments/sha1_rr_only_v1_2026-10-10'/name;out=R/'experiments/sha1_native_cold_v1_2026-10-10'/name;out.mkdir(parents=True);binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';graph=src/'rr_graph.xml';bindings={str(p):sha(p) for p in [Path(__file__),prp,*proofs,binary,arch,graph,src/'design.blif',src/'design.net',src/'design.place']}
for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/f,out/f)
assert params['order'][0]=='cold';cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width',str(params['route_chan_width']),'--num_workers',str(params['num_workers']),'--seed',str(params['seed']),'--max_router_iterations',str(params['max_router_iterations']),'--check_route','full'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,timeout_seconds=params['timeout_per_case_seconds'],scope='First frozen cold routing attempt, complete candidate, all inherited ROUTECAST flags removed. Fixed experimental async architecture, full scope. No timeout/failure omitted. Native-only timer not complete workflow speed; CPD remains synthetic uncharacterized timing, not physical/heldout/netgain pass.'),indent=2)+'\n');tick=time.perf_counter()
with (out/'native.log').open('w') as log:
 try:code=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=params['timeout_per_case_seconds']).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
text=(out/'native.log').read_text();assert 'NET-aware seed imported' not in text;result=dict(bindings=bindings,exit_code=code,native_process_seconds=time.perf_counter()-tick,status='NATIVE_FAILED_OR_TIMEOUT',route_file_exists=(out/'output.route').is_file())
if code==0 and 'VPR succeeded' in text and result['route_file_exists']:
 result['status']='NATIVE_SUCCESS_PENDING_INDEPENDENT_AUDIT';result['diagnostic_cpd_ns']=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);result['wirelength']=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1])
assert all(sha(k)==v for k,v in bindings.items());result['files']={str(p):sha(p) for p in out.iterdir() if p.is_file()};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],code,flush=True)
