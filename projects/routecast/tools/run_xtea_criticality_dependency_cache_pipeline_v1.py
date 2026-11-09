"""Full second-design portability experiment and unchanged independent auditors."""
import json,sys,time,subprocess,resource
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
from observe_neuron_compiled_pipeline_v1 import snapshot
R=Path(__file__).resolve().parents[1]
O=R/'experiments/xtea_criticality_dependency_cache_pipeline_v1_2026-10-15';O.mkdir()
ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json'
base=R/'experiments/xtea_node_base_wide_v1_2026-10-13/verification.json'
crit=R/'experiments/xtea_retained_native_inputs_v1_2026-10-13/criticality'
model=O/'model';scripts=['run_design_scoped_dependency_cached_retained_tree_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_scaled_present_retained_tree_full_schedule_v1.py']
bindings=closure([Path(__file__),*[R/'tools'/s for s in scripts]])
for p in [R/'experiments/cached_multiplicative_occupancy_contract_v1_2026-10-13/verification.json',base.with_name('independent_verification.json'),R/'experiments/retained_tree_cross_design_readiness_v1_2026-10-13/model_derivation_v1.json']:
 v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items())
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,endpoint=str(ep),node_base_proof=str(base),criticality_directory=str(crit),connections=2450,nets=1448,rounds=2,present_factor=1,heldout=False,policy='Same retained primary, fanout16, delayed history, fixed per-pin initial criticality, wholeNET fallback, exact objective and overflow admission.',scope='Complete exposed XTEA input/model portability and correctness validation; no accuracy selection, heldout family, native QoR or paired speed proof.'),indent=2)+'\n')
stages=[('model',[scripts[0],str(ep),str(model),str(base),str(crit),'1']),('initial_audit',[scripts[1],str(model),'initial',str(model/'initial_physical_verification.json')]),('sketch_audit',[scripts[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),('event_audit',[scripts[2],str(model),'xtea',str(model/'verification.json'),'1'])]
for name,args in stages:
 assert all(sha(p)==h for p,h in bindings.items())
 live_case=R/'experiments/titan23_neuron_scaled_present_factor1_pipeline_v1_2026-10-15';launch=json.loads((live_case/'launch_observation_v1.json').read_text());reserve=8*2**30
 if not (live_case/'model_terminal.json').exists():
  proc=Path('/proc')/str(launch['model_pid']);st=proc.joinpath('stat').read_text().rsplit(')',1)[1].split();assert int(st[19])==launch['model_startticks'] and st[0]!='Z'
  status=proc.joinpath('status').read_text().splitlines();vm=int(next(l for l in status if l.startswith('VmSize:')).split()[1])*1024;reserve=max(0,20*2**30-vm)
 current=int(Path('/sys/fs/cgroup/memory.current').read_text());maximum=int(Path('/sys/fs/cgroup/memory.max').read_text());limit=2**30;required=reserve+limit+8*2**30
 admission=dict(stage=name,remaining_live_neuron_model_reservation_bytes=reserve,child_limit_bytes=limit,extra_margin_bytes=8*2**30,shared_headroom_bytes=maximum-current,required_headroom_bytes=required,admitted=maximum-current>=required)
 (O/(name+'_admission.json')).write_text(json.dumps(admission,indent=2)+'\n')
 if not admission['admitted']:raise RuntimeError('XTEA stage not launched: shared memory admission unavailable')
 print('XTEA START',name,flush=True);tick=time.perf_counter()
 with (O/(name+'.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(limit,limit)))
 (O/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick))+'\n')
 if code:raise SystemExit(code)
assert all(sha(p)==h for p,h in bindings.items())
(O/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True))+'\n')
print('XTEA full model and independent audits PASS',flush=True)

reference=R/'experiments/xtea_design_scoped_retained_pipeline_v1_2026-10-13/model'
ref=json.loads((reference/'receipt.json').read_text());actual=json.loads((model/'receipt.json').read_text())
assert all(sha(p)==h for p,h in ref['bindings'].items())
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:
 assert sha(model/name)==sha(reference/name)
assert len(ref['rounds'])==len(actual['rounds'])==2
for a,b in zip(ref['rounds'],actual['rounds']):
 assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
(O/'exact_reference_parity.json').write_text(json.dumps(dict(reference_receipt_sha256=sha(reference/'receipt.json'),candidate_receipt_sha256=sha(model/'receipt.json'),all_complete_frames_byte_equal=True,all_events_and_round_metadata_equal=True,scope='Bounded read-dependency cache over arbitrary-integer reference searches, factor1; explicit active owner Context validation; exact full original-model parity. Complete original XTEA frames/events and all independent audits equal. No full-neuron memory or paired performance claim.'))+'\n')
print('WIDE XTEA FULL EXACT PARITY PASS',flush=True)
