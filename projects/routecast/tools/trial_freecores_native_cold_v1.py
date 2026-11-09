import json,sys,subprocess,shutil,os,time,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
name=sys.argv[1];prp=R/'experiments/freecores_prospective_evaluation_prereg_v1_2026-10-08/protocol.json';pr=json.loads(prp.read_text());assert all(sha(k)==v for k,v in pr['bindings'].items());assert name in pr['cases'];resident=R/'experiments/freecores_resident_v1_2026-10-08'/name/'resident';proofs=[resident/'initial_physical_verification.json',resident/'sketch_physical_verification.json',resident/'verification.json']
for p in proofs:
 d=json.loads(p.read_text());assert d['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(k)==v for k,v in d['bindings'].items())
d=json.loads(proofs[-1].read_text());assert d['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and d['completed']==len(json.loads((R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json').read_text())['connections'])
for other in pr['cases']:
 p=R/'experiments/freecores_resident_v1_2026-10-08'/other/'resident/verification.json';audit=json.loads(p.read_text());assert audit['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'] and all(sha(k)==v for k,v in audit['bindings'].items())
 params=pr['native']
src=R/'experiments/freecores_rr_only_v1_2026-10-08'/name;out=R/'experiments/freecores_native_cold_v1_2026-10-08'/name;out.mkdir(parents=True);binary=R/'build/native_candidate_retained_search_2026-10-06/sequence_vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';graph=src/'rr_graph.xml';bindings={str(p):sha(p) for p in [Path(__file__),prp,*proofs,binary,arch,graph,src/'design.blif',src/'design.net',src/'design.place']}
for f in ['design.blif','design.net','design.place']:shutil.copyfile(src/f,out/f)
assert params['order'][0]=='cold';cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width',str(params['route_chan_width']),'--num_workers',str(params['num_workers']),'--seed',str(params['seed']),'--max_router_iterations',str(params['max_router_iterations']),'--check_route','full'];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,timeout_seconds=params['timeout_per_case_seconds'],scope='First frozen cold routing attempt, complete candidate, all inherited ROUTECAST flags removed. Fixed experimental async architecture, full scope. No timeout/failure omitted. Native-only timer not complete workflow speed; CPD remains synthetic uncharacterized timing, not physical/heldout/netgain pass.'),indent=2)+'\n');tick=time.perf_counter()
with (out/'native.log').open('w') as log:
 try:code=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=params['timeout_per_case_seconds']).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
text=(out/'native.log').read_text();assert 'NET-aware seed imported' not in text;result=dict(bindings=bindings,exit_code=code,native_process_seconds=time.perf_counter()-tick,status='NATIVE_FAILED_OR_TIMEOUT',route_file_exists=(out/'output.route').is_file())
if code==0 and 'VPR succeeded' in text and result['route_file_exists']:
 result['status']='NATIVE_SUCCESS_PENDING_INDEPENDENT_AUDIT';result['diagnostic_cpd_ns']=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1]);result['wirelength']=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1])
assert all(sha(k)==v for k,v in bindings.items());result['files']={str(p):sha(p) for p in out.iterdir() if p.is_file()};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],code,flush=True)
