"""Frozen full MMC paired direct-lattice audit parity; all original audit bodies retained."""
import json,sys,subprocess,shutil,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
source=R/'experiments/ultraembedded_mmc_actual_old_linear_fallback_workflow_v11_2026-10-09/seed/model/mmc'
admission=source/'shared_audit_receipt.json';proof=json.loads(admission.read_text())
assert proof['all_three_complete_audits_pass'] and all(sha(p)==h for p,h in proof['bindings'].items())
D=R/'experiments/mmc_complete_direct_lattice_audits_reverse_v2_2026-10-10';D.mkdir()
runners={'direct':R/'tools/run_shared_actual_old_linear_direct_lattice_audits_v4.py','control':R/'tools/run_shared_actual_old_linear_fraction_cache_audits_v3.py'}
bindings={**closure([Path(__file__),*runners.values()]),str(admission):sha(admission)}
forward=R/'experiments/mmc_complete_direct_lattice_audits_v1_2026-10-10/verification.json'
fault=R/'experiments/direct_lattice_full_frame_fault_v1_2026-10-10/verification.json'
for admission_path,gate in [(forward,'all_three_complete_proof_outputs_equal_except_source_bindings'),(fault,'wrong_exact_scale_rejected_by_actual_full_frame_delay_assertion')]:
 admitted=json.loads(admission_path.read_text());assert admitted[gate] and all(sha(p)==h for p,h in admitted['bindings'].items())
 assert all(sha(p)==h for p,h in admitted['files'].items());bindings[str(admission_path)]=sha(admission_path)
for mode in runners:
 model=D/mode;model.mkdir()
 for name in ['protocol.json','receipt.json','initial.json','floors.json','round0.json','round1.json','sketch.json']:
  a=source/name;b=model/name;shutil.copyfile(a,b);assert sha(a)==sha(b);bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,order=list(runners),scope='Two fresh independent XML contexts, complete frozen development MMC model copied identically before timers. Both arms retain exact Fraction arc cache; candidate only replaces all-edge lattice enumeration with direct immutable arrays. Direct lattice then cached Fraction control single paired local audit experiment, no cProfile. All body AST checks preserved. Historical state used explicitly for parity diagnosis; no fresh prediction/native/full workflow gain or replicate stability claim.'),indent=2)+'\n')
rows=[]
for mode,runner in runners.items():
 tick=time.perf_counter()
 with (D/(mode+'.log')).open('w') as f:
  p=subprocess.run([sys.executable,str(runner),str(D/mode),'mmc'],cwd=R,stdout=f,stderr=subprocess.STDOUT,timeout=1200)
 elapsed=time.perf_counter()-tick;rows.append(dict(mode=mode,exit_code=p.returncode,local_subprocess_seconds=elapsed))
 (D/'stages.json').write_text(json.dumps(rows,indent=2)+'\n');assert p.returncode==0
for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
 pair=[]
 for mode in runners:
  path=D/mode/name;data=json.loads(path.read_text());assert all(sha(p)==h for p,h in data['bindings'].items());bindings[str(path)]=sha(path)
  pair.append({k:v for k,v in data.items() if k!='bindings'})
 assert pair[0]==pair[1],name
for mode in runners:
 p=D/mode/'shared_audit_receipt.json';s=json.loads(p.read_text())
 assert s['all_three_complete_audits_pass'] and s['complete_audit_bodies_AST_preserved'] and s['fresh_independent_graph_context']
 assert all(sha(p)==h for p,h in s['bindings'].items());bindings[str(p)]=sha(p)
cache=s['cache_diagnostics'];assert cache['contexts']==1 and cache['calls']==cache['hits']+cache['misses'] and cache['misses']==cache['entries']
assert all(sha(p)==h for p,h in bindings.items())
result=dict(bindings=bindings,files={str(p):sha(p) for p in [D/'protocol.json',D/'stages.json',D/'control.log',D/'direct.log']},all_three_complete_proof_outputs_equal_except_source_bindings=True,rows=rows,cache_diagnostics=cache,observed_single_pair_direct_over_cached_control=rows[0]['local_subprocess_seconds']/rows[1]['local_subprocess_seconds'],scope='Complete frozen development MMC independent audit parity only. Both arms load own independent original XML contexts and retain all paths/events. Single direct-then-cached-control local timer observations, no stability/causal/full workflow/heldout/silicon gain claim.')
(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','files']},indent=2),flush=True)
