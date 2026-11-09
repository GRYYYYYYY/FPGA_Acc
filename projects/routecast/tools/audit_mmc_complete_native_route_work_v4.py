"""Actual native printed reroute work; repeated attempts, not unique coverage."""
import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from native_route_work_metrics import extract
roots={'actual_old_linear_direct_lattice':R/'experiments/ultraembedded_mmc_actual_old_linear_direct_lattice_workflow_v13_2026-10-10','actual_old_linear_cached':R/'experiments/ultraembedded_mmc_actual_old_linear_fraction_cache_workflow_v12_2026-10-10','default_linear':R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09','actual_old_linear':R/'experiments/ultraembedded_mmc_actual_old_linear_fallback_workflow_v11_2026-10-09'}
bindings=closure([Path(__file__)]);rows=[]
for model,d in roots.items():
 vp=d/'verification.json';verified=json.loads(vp.read_text());assert verified['all_cases_both_complete_arms_authenticated'];bindings[str(vp)]=sha(vp)
 for mode in ['cold','seed']:
  native=d/mode/'native/mmc';rp=native/'receipt.json';r=json.loads(rp.read_text());log=native/'native.log'
  assert verified['bindings'][str(rp)]==sha(rp)
  assert r['files'][str(log)]==sha(log)
  physical_path=native/'verification.json';physical=json.loads(physical_path.read_text())
  assert verified['bindings'][str(physical_path)]==sha(physical_path)
  assert physical['original_native_FULL_check_pass'] and physical['overflow_units']==0 and physical['physical_connections']==115572
  bindings.update({str(rp):sha(rp),str(log):sha(log),str(physical_path):sha(physical_path)})
  text=log.read_text();work=extract(text)
  assert work['routing_success'] and work['native_vpr_succeeded'] and work['iterations']==physical['iterations']
  lines=[line.split() for line in text.splitlines() if re.match(r'^\s*\d+\s+[0-9.]+\s+[0-9.]+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\(',line)]
  assert len(lines)==work['iterations']
  assert [int(x[0]) for x in lines]==list(range(1,work['iterations']+1))
  for index,field in [(4,'heap_pushes'),(5,'rerouted_nets'),(6,'rerouted_connections'),(7,'overused_nodes')]:
   assert [int(x[index]) for x in lines]==[x[field] for x in work['iteration_rows']]
  assert sum(int(x[4]) for x in lines)==work['heap_pushes']
  assert sum(int(x[6]) for x in lines)==work['rerouted_connection_attempts']
  rows.append(dict(model=model,arm=mode,physical_connections=115572,**work,rerouted_net_attempts=sum(int(x[5]) for x in lines),first_iteration_connection_attempts=int(lines[0][6]),later_iteration_connection_attempts=sum(int(x[6]) for x in lines[1:])))
assert all(sha(p)==h for p,h in bindings.items())
D=R/'experiments/mmc_complete_native_route_work_v4_2026-10-10';D.mkdir()
result=dict(bindings=bindings,all_eight_complete_native_iteration_tables_independently_token_verified=True,rows=rows,scope='Archived complete development MMC native routing work. Re-Rtd nets/connections are printed repeated attempts, including first iteration, not distinct connection coverage or model transaction counts. Later-iteration totals separately reported. Internal rounded times descriptive and nested, never added to external clocks. Eight successful runs do not estimate general failure probability, heldout, real async timing or full workflow gain. Direct-lattice v13 and cached v12 native counters explicitly included after full scientific verification.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{k:x[k] for k in ['model','arm','iterations','rerouted_connection_attempts','rerouted_net_attempts','heap_pushes','first_iteration_connection_attempts','later_iteration_connection_attempts']} for x in rows],indent=2))
