"""Instrument only the frozen feedback region; preserve complete outputs and events."""
import ast,cProfile,json,pstats,time,sys
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_feedback_hot_profile_v1_2026-10-21';D.mkdir()
P=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/protocol.json';p=json.loads(P.read_text());assert all(sha(k)==v for k,v in p['bindings'].items())
source=Path(p['command'][1]);bindings={**p['bindings'],str(P):sha(P),str(Path(__file__)):sha(__file__)}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'scope':'Frozen MMC exact replay with cProfile enabled at feedback_tick and disabled before search.close. Full setup/model/output executed and counted. Profiling perturbs clocks; use for attribution, not speed claims. No native calls or policy edits. Complete states and event payloads must match original.','native_calls':0},indent=2)+'\n')
profile=cProfile.Profile();tree=ast.parse(source.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict');new=[];starts=stops=0
for n in function.body:
 if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='feedback_tick' for t in n.targets):
  new.extend(ast.parse('_hot_profiler.enable()').body);starts+=1
 if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='search.close':
  new.extend(ast.parse('_hot_profiler.disable()').body);stops+=1
 new.append(n)
assert starts==stops==1
function.body=new;ast.fix_missing_locations(tree)
ns={'__file__':str(source),'__name__':'mmc_profile_instrumented','_hot_profiler':profile};exec(compile(tree,str(source),'exec'),ns)
args=p['command'][2:];old=Path(args[1]);args[1]=str(D/'model');tick=time.perf_counter()
result=ns['predict'](*args);elapsed=time.perf_counter()-tick;profile.dump_stats(str(D/'feedback.prof'))
stat=pstats.Stats(profile);top=[]
for (file,line,name),(primitive,calls,selftime,cumulative,callers) in sorted(stat.stats.items(),key=lambda x:x[1][3],reverse=True)[:45]:
 top.append({'file':file,'line':line,'function':name,'calls':calls,'self_seconds':selftime,'cumulative_seconds':cumulative})
parity={}
for name in ['initial.json','floors.json','round0.json','round1.json','sketch.json','structural_cost_metrics.json']:
 parity[name]=sha(old/name)==sha(D/'model'/name);assert parity[name],name
before=json.loads((old/'receipt.json').read_text());after=json.loads((D/'model/receipt.json').read_text())
def semantic(rounds):return [{k:v for k,v in r.items() if k not in ['seconds','state_file']} for r in rounds]
assert semantic(before['rounds'])==semantic(after['rounds'])
assert all(sha(k)==v for k,v in bindings.items())
receipt={'full_state_bytes_exact':parity,'all_round_events_and_counts_exact':True,'instrumented_predict_wall_seconds':elapsed,'model_reported_times':{k:v for k,v in after.items() if k.endswith('seconds')},'profile_top_cumulative':top,'profile_total_self_seconds':stat.total_tt,'bindings':{**bindings,str(D/'feedback.prof'):sha(D/'feedback.prof'),str(D/'model/receipt.json'):sha(D/'model/receipt.json')},'scope':'Profiling attribution only, not uninstrumented timing or end-to-end gain. Full output files and event payloads unchanged; original cached-floor/source-contract limitations retained.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('HOT PROFILE EXACT PARITY PASS',elapsed,flush=True)
