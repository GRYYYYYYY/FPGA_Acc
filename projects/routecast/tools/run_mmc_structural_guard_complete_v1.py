"""Fresh endogenous MMC model, then complete independent physical/event audits."""
import json,sys,time,subprocess
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from source_binding_v2 import closure
from pre_route_endpoints import sha

def main():
 out=R/'experiments/mmc_structural_guard_complete_v1_2026-10-10'
 out.mkdir(exist_ok=False)
 model=out/'model'
 producer=R/'tools/run_structural_overflow_guard_model_v1.py'
 audit=R/'tools/run_structural_guard_audits_v1.py'
 endpoint=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json'
 bindings=closure([Path(__file__),producer,audit,R/'tools/verify_structural_guard_events_v1.py'])
 for p in [endpoint,R/'experiments/structural_objective_contract_v1_2026-10-10/verification.json',R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so',R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so']:
  bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 (out/'startup.json').write_text(json.dumps(dict(bindings=bindings,scope='Fresh complete candidate endogenous model; all sources bound before launch. Independent full audits required; no native routing or speed claim.'),indent=2)+'\n')
 stages=[]
 for name,command in [('model',[sys.executable,str(producer),str(endpoint),str(model)]),('audits',[sys.executable,str(audit),str(model),'mmc'])]:
  tick=time.perf_counter()
  with (out/(name+'.log')).open('w') as log:
   process=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print('START',name,'pid',process.pid,flush=True)
   status=process.wait()
  stages.append(dict(stage=name,command=command,exit_status=status,seconds=time.perf_counter()-tick))
  (out/'stages.json').write_text(json.dumps(stages,indent=2)+'\n')
  print('DONE',json.dumps(stages[-1]),flush=True)
  if status:raise RuntimeError(f'{name} failed; inspect log; no automatic restart')
 receipt=json.loads((model/'receipt.json').read_text())
 proof=json.loads((model/'shared_audit_receipt.json').read_text())
 assert proof['all_three_complete_audits_pass']
 for item in [receipt,proof]:
  assert all(sha(p)==h for p,h in item['bindings'].items());bindings.update(item['bindings'])
 assert all(sha(p)==h for p,h in receipt['files'].items());bindings.update(receipt['files'])
 baseline=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model/floors.json'
 assert json.loads((model/'floors.json').read_text())==json.loads(baseline.read_text())
 initial=json.loads((model/'initial.json').read_text());final=json.loads((model/'sketch.json').read_text())
 assert initial['completed_connections']==final['completed_connections']==115572
 metrics=json.loads((model/'structural_cost_metrics.json').read_text())
 events=[e for row in receipt['rounds'] for e in row['events']]
 for p in [out/'startup.json',out/'stages.json',model/'receipt.json',model/'shared_audit_receipt.json',baseline]:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items())
 result=dict(bindings=bindings,complete_115572_connections_and_independent_physical_events_pass=True,all_floors_equal_original=True,overflow=[initial['overflow_units'],*[row['overflow_after'] for row in receipt['rounds']]],original_model_final_overflow=56351,events=len(events),statuses=dict(Counter(e['status'] for e in events)),primary_budget_fallback_events=sum('fallback' in e for e in events),metrics=metrics,stages=stages,scope='Exposed MMC fresh candidate feedback, independent full physical/event audits; no native quality, heldout or wholeworkflow speed admission.')
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
 print('COMPLETE MMC STRUCTURAL PASS',result['overflow'],result['statuses'],flush=True)
if __name__=='__main__':main()
