"""Same warm staged routes/history/timing; compare allNET with moved-closure updates."""
import json,sys,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];O=R/'experiments/xtea_warm_update_pair_v1_2026-10-13';O.mkdir()
ep=R/'experiments/xtea_swap_native_demand_v1_2026-10-13/endpoints.json';base=R/'experiments/xtea_swap_node_base_v1_2026-10-13/verification.json';crit=R/'experiments/xtea_fixed_timing_epoch_v1_2026-10-13';warm=R/'experiments/xtea_swap_warm_seed_v1_2026-10-13'
scripts=['run_warm_epoch_retained_update_v1.py','verify_resident_demand_frame_direct_lattice_v7.py','verify_warm_epoch_retained_update_v1.py'];bindings=closure([Path(__file__),*[R/'tools'/s for s in scripts]])
for p in [warm/'verification.json',crit/'design_bundle_admission_v1.json']:
 v=json.loads(p.read_text());assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=['all','local'],scheduling_only_factor=True,scope='Same moved-placement warm seed, carried old history/epochs and fixed timing snapshot. AllNET versus49NET closure for2rounds. Local update is approximate under congestion coupling; no equality to global reoptimization assumed. Prior state and preparation costs separate, one-shot timing only; no placement acceptance/heldout/netgain claim.'),indent=2)+'\n');results=[]
for arm in ['all','local']:
 d=O/arm;d.mkdir();model=d/'model'
 stages=[('model',[scripts[0],str(ep),str(model),str(base),str(crit),str(warm),arm]),('initial_audit',[scripts[1],str(model),'initial',str(model/'initial_physical_verification.json')]),('sketch_audit',[scripts[1],str(model),'sketch',str(model/'sketch_physical_verification.json')]),('event_audit',[scripts[2],str(model),'xtea',str(model/'verification.json')])]
 for name,args in stages:
  assert all(sha(p)==h for p,h in bindings.items());print('WARM UPDATE START',arm,name,flush=True);tick=time.perf_counter()
  with (d/(name+'.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/args[0]),*args[1:]],cwd=R,stdout=log,stderr=subprocess.STDOUT)
  (d/(name+'_terminal.json')).write_text(json.dumps(dict(exit_status=code,seconds=time.perf_counter()-tick))+'\n')
  if code:raise SystemExit(code)
 for name in ['initial.json','floors.json']:assert sha(model/name)==sha(warm/name)
 r=json.loads((model/'receipt.json').read_text());results.append(dict(arm=arm,rounds=[dict(round=x['round_index'],nets=len(x['events']),primary_search_calls=sum(e['primary_search_calls'] for e in x['events']),overflow=x['overflow_after']) for x in r['rounds']],total_paid_resident_seconds=r['total_paid_resident_seconds'],feedback_seconds=r['feedback_seconds']))
 (d/'pipeline_terminal.json').write_text(json.dumps(dict(exit_status=0,all_stages_completed=True))+'\n');print('WARM UPDATE PASS',json.dumps(results[-1]),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
for p in O.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,results=results,both_complete_models_and_all_audits_pass=True,initial_and_floors_byte_equal_shared_warm_seed=True,scope='Fixed-epoch warm update correctness and descriptive full/local comparison; native QoR/labels/end-to-end timing still pending.'),indent=2)+'\n')
