"""Whole-model cProfile diagnosis with full certified semantic equality."""
import json,sys,time,subprocess,pstats
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1]
ref=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/model'
script=R/'tools/run_mmc_native_cached_feedback_v1_2026_10_18.py';bindings=closure([Path(__file__),script])
for name in ['initial.json','sketch.json','events.json']:
 p=R/'experiments/mmc_native_cached_feedback_audits_v1_2026-10-18'/name;v=json.loads(p.read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(q)==h for q,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
expected=json.loads((ref/'receipt.json').read_text());bindings[str(ref/'receipt.json')]=sha(ref/'receipt.json');bindings.update(expected['files']);assert all(sha(p)==h for p,h in bindings.items())
O=R/'experiments/mmc_native_local_full_profile_v1_2026-10-18';O.mkdir();ep=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';base=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18/base/verification.json';crit=R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18/timing'
cmd=[sys.executable,'-m','cProfile','-o',str(O/'profile.pstats'),str(script),str(ep),str(O/'model'),str(base),str(crit),str(R/'experiments/mmc_native_feedback_inputs_v1_2026-10-18/warm'),'local']
(O/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=cmd,scope='Full exposed-XTEA computational hotspot diagnosis with cProfile overhead. Not a comparable uninstrumented timing sample or end-to-end speed proof.'),indent=2)+'\n')
tick=time.perf_counter()
with (O/'model.log').open('x') as log:code=subprocess.call(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
(O/'terminal.json').write_text(json.dumps(dict(exit_status=code,wall_seconds=time.perf_counter()-tick))+'\n');assert code==0
model=O/'model';r=json.loads((model/'receipt.json').read_text());assert r['bindings']==expected['bindings']
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json']:assert sha(model/name)==sha(ref/name)
for a,b in zip(r['rounds'],expected['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
assert len(r['rounds'])==len(expected['rounds'])==2
stats=pstats.Stats(str(O/'profile.pstats'));functions=[]
for (file,line,name),(primitive,total,self_s,cumulative,callers) in stats.stats.items():functions.append(dict(file=file,line=line,function=name,primitive_calls=primitive,total_calls=total,self_seconds=self_s,cumulative_seconds=cumulative))
assert all(sha(p)==h for p,h in bindings.items())
for p in O.rglob('*'):
 if p.is_file():bindings[str(p)]=sha(p)
result=dict(bindings=bindings,all_full_model_frames_and_events_equal_certified_reference=True,total_profile_seconds=stats.total_tt,top_self=sorted(functions,key=lambda x:x['self_seconds'],reverse=True)[:25],top_cumulative=sorted(functions,key=lambda x:x['cumulative_seconds'],reverse=True)[:25],scope='Instrumented Python/software full-model diagnosis; profiler overhead included, no uninstrumented speedup claim.')
(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result['top_self'][:10]),flush=True)
