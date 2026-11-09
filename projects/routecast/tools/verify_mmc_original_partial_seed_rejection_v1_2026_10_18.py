"""Confirm original engine rejects a valid partialNET seed at its delay guard."""
import json,sys,os,subprocess,shutil,resource,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
S=R/'experiments/mmc_old_branch_prune_seeds_v1_2026-10-18';sp=S/'seed_admission_verification_v1.json';sv=json.loads(sp.read_text());assert sv['all3_partialNET_old_branch_seeds_independently_admitted'] and all(sha(p)==h for p,h in sv['bindings'].items());D=R/'experiments/mmc_partial_seed_original_rejection_v1_2026-10-18';D.mkdir();I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/mmc';P=R/'experiments/mmc_v2_native_utility_v1_2026-10-18/case_01/protocol.json';cmd=json.loads(P.read_text())['commands']['cold'];B=R/'build/native_candidate_retained_search_2026-10-06';b=json.loads((B/'receipt.json').read_text());assert sha(cmd[0])==b['binary_sha256'];bindings={**sv['bindings'],**closure([Path(__file__)]),str(sp):sha(sp),str(P):sha(P),str(B/'receipt.json'):sha(B/'receipt.json'),str(Path(cmd[0])):b['binary_sha256']}
for name in ['design.net','design.blif','design.place']:shutil.copyfile(I/name,D/name);bindings[str(D/name)]=sha(D/name)
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env['ROUTECAST_NATIVE_SEED']=str(S/'case_01/seed.route')
def limit():resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,command=cmd,expected='Original missing-sink delay-map guard rejects partialNET seed; no native unrouteability inference',core_dumps_disabled_for_this_child=True),f,indent=2)
tick=time.perf_counter()
with (D/'native.log').open('x') as f:code=subprocess.run(cmd,cwd=D,env=env,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit,timeout=None).returncode
log=(D/'native.log').read_text();assert code!=0 and 'incomplete seed delay map' in log and 'NET-aware seed imported' in log and not (D/'output.route').exists();bindings[str(D/'native.log')]=sha(D/'native.log');assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(status='expected_guard_rejection_confirmed',bindings=bindings,exit_code=code,seconds=time.perf_counter()-tick,old_engine_partial_NET_import_reaches_explicit_delay_map_guard=True,scope='Unsupported original wrapper input, not physical unrouteability; admitted partial seed still needs complete routing under new support build. No old binary modification or speed claim.'),f,indent=2)
print('EXPECTED ORIGINAL PARTIAL-NET GUARD REJECTION',code,flush=True)
