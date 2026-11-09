"""Continuous prepared-seed DEVELOPMENT replay; all stages and proofs charged."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'experiments/mux32_continuous_feedback_2026-10-07'
OUT.mkdir(exist_ok=False)
keys=['critical','ascending','reverse','longest','shortest','revisit','retry']
original=['mux32_critical_repair','mux32_incremental_budget_tree','mux32_reverse_tree','mux32_longest_first_tree','mux32_shortest_first_tree','mux32_id_revisit_tree','mux32_limit_retry_tree']
new={key:'mux32_continuous_'+key+'_2026-10-07' for key in keys}
alias={name+'_2026-10-07':new[key] for key,name in zip(keys,original)}
alias.update({'mux32_limit_retry_native_2026-10-07':'mux32_continuous_native_2026-10-07','mux32_limit_retry_canonical_2026-10-07':'mux32_continuous_canonical_2026-10-07'})
def remap(source):
 for before,after in alias.items():source=source.replace(before,after)
 return source
jobs=[];generated=[]
# Critical repair remains the exact shortest-RC implementation.
for key in keys:
 if key=='critical':source=remap((ROOT/'tools/trial_mux32_critical_repair.py').read_text())
 else:
  source=(ROOT/'tools/trial_mux32_integer_path_tree.py').read_text().replace('mux32_integer_path_tree_2026-10-07',new[key])
  previous=keys[keys.index(key)-1]
  source=source.replace('mux32_id_revisit_tree_2026-10-07',new[previous])
  if key!='retry':
   source=source.replace("selector=ROOT/", "selector=ROOT/",1)
   lines=source.splitlines();source='\n'.join(line for line in lines if not line.startswith('selector='))+'\n'
   source=source.replace('(pf,gf,mf,af,graph,selector)','(pf,gf,mf,af,graph)').replace('&selected_nets','').replace('max_net_attempts=9,max_labels=20000','max_net_attempts=52,max_labels=10000').replace('len(labels)>=20000','len(labels)>=10000')
   source=source.replace('Retry only previously label-limited affected NETs','Rebuild all affected NETs').replace('cap20000labels','cap10000labels')
  order={'reverse':"-q['connection_id']",'longest':"(-q['answer']['delay'],q['connection_id'])",'shortest':"(q['answer']['delay'],q['connection_id'])"}.get(key)
  if order:source=source.replace("key=lambda q:q['connection_id'])",f'key=lambda q:{order})')
  source=source.replace('route connections ascending ID',f'route connections under fixed {key} ordering')
 script=ROOT/f'tools/continuous_mux32_{key}.py';script.write_text(source);generated.append(script);jobs.append((key,'producer',script))
 verifier=ROOT/f'tools/continuous_mux32_{key}_verify.py';verifier.write_text(remap((ROOT/f'tools/verify_{original[keys.index(key)]}.py').read_text()));generated.append(verifier);jobs.append((key,'verifier',verifier))
for tag,filename in [('native','trial_mux32_limit_retry_native.py'),('native_verify','verify_mux32_limit_retry_native.py'),('canonical','trial_mux32_limit_retry_canonical.py'),('canonical_verify','verify_mux32_limit_retry_canonical.py'),('state_join','verify_mux32_limit_retry_state_join.py')]:
 script=ROOT/f'tools/continuous_mux32_{tag}.py';script.write_text(remap((ROOT/'tools'/filename).read_text()));generated.append(script);jobs.append((tag,'final',script))
seed=ROOT/'experiments/owner50_retained_rr_2026-10-07_predictor/w32_m2/result.json'
protocol=dict(sources=closure([Path(__file__),*generated]),seed_sha256=sha(seed),sequence=[{'stage':stage,'kind':kind,'script':str(script)} for stage,kind,script in jobs],scope='Continuous DEVELOPMENT replay from prepared initial predictor. All graph reloads, generation, intermediate independent proofs and final native/canonical/state join included in external wall clock. Original mapped input, seed predictor, old timing graph/conversion/compiler preparation excluded. No heldout/raw-input end-to-end or matched baseline claim. No target cold oracle used by policy; archived old published quality used final evaluator.')
(OUT/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();rows=[];status='FAILED'
try:
 for stage,kind,script in jobs:
  tick=time.perf_counter();log=OUT/f'{stage}_{kind}.log'
  with log.open('w') as stream:code=subprocess.run([sys.executable,str(script)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=600).returncode
  row=dict(stage=stage,kind=kind,exit_code=code,external_seconds=time.perf_counter()-tick,log_sha256=sha(log));rows.append(row);print(row,flush=True)
  (OUT/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
  if code:raise RuntimeError(f'{stage}/{kind} exit {code}')
 assert all(sha(f)==h for f,h in protocol['sources'].items())
 status='COMPLETE_STATIC_CANONICAL_CANDIDATE'
except Exception as ex:error=repr(ex)
result=dict(protocol_sha256=sha(OUT/'protocol.json'),status=status,rows=rows,external_wall_seconds=time.perf_counter()-start,error=locals().get('error'),scope=protocol['scope'])
(OUT/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result['external_wall_seconds'],result['error'],flush=True)
if status!='COMPLETE_STATIC_CANONICAL_CANDIDATE':raise SystemExit(1)
