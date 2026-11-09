"""Fixed three-case forecast matrix for admitted isolated terminal batches."""
import json,sys,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 proof=R/'experiments/mmc_terminal_commit_replay_v1_2026-10-18/verification.json'
 contract=R/'experiments/mmc_terminal_batch_quality_source_contract_v1_2026-10-18/verification.json'
 v=json.loads(proof.read_text());c=json.loads(contract.read_text());assert v['status']==c['status']=='pass'
 scripts=[R/'tools/evaluate_mmc_terminal_batch_quality_case_v1_2026_10_18.py',R/'tools/verify_mmc_terminal_batch_quality_case_v1_2026_10_18.py']
 bindings={**v['bindings'],**c['bindings'],str(proof):sha(proof),str(contract):sha(contract),**closure([Path(__file__),*scripts])}
 cache=Cache()
 with cache.installed():assert all(sha(p)==h for p,h in bindings.items())
 d=R/'experiments/mmc_terminal_batch_quality_v1_2026-10-18';d.mkdir();(d/'logs').mkdir()
 plan=dict(candidate='native_retained_terminal_batch',fixed_controls=['native_retained_on','raw_min_on','previous_native'],primary_label='cold',supplemental_labels=['partial_seed_default','partial_seed_firstpass_preserve'],expected_metric_vectors=108,cohort_rule='Original all3-case nonregression in concrete/spatial Spearman and precision@K, at least one strict improvement per control. Cold label remains primary; other policy labels cannot replace failed gates.',scope='Same3exposed placements, fixed admitted15class/25path batch frames. No retuning or label selection, new native run, unseen-family or full-flow claim.')
 with (d/'protocol.json').open('x') as stream:json.dump(dict(bindings=bindings,plan=plan),stream,indent=2)
 for case in ['case_01','case_02','case_03']:
  old=R/'experiments/mmc_old_owner_pressure_quality_v1_2026-10-18'/case/'protocol.json';p=json.loads(old.read_text())
  assert p['primary_controls']==plan['fixed_controls'] and set(p['labels'])=={'cold',*plan['supplemental_labels']}
  del p['predictions']['native_retained_owner_pressure_on']
  frame=R/'experiments/mmc_terminal_batch_commit_v2_2026-10-18'/case/'frame.json';assert v['bindings'][str(frame)]==sha(frame)
  p['predictions'][plan['candidate']]=str(frame);assert len(p['predictions'])==6
  p.update(bindings={str(proof):sha(proof),str(contract):sha(contract),str(d/'protocol.json'):sha(d/'protocol.json'),str(old):sha(old)},frozen_cohort_protocol=str(d/'protocol.json'),frozen_cohort_protocol_sha256=sha(d/'protocol.json'),primary_candidate=plan['candidate'],batch_admission=str(proof),evidence_scope=plan['scope'])
  p.pop('context_admission',None)
  folder=d/case;folder.mkdir()
  with (folder/'protocol.json').open('x') as stream:json.dump(p,stream,indent=2)
 def run(case):
  print('TERMINAL BATCH QUALITY START',case,flush=True)
  for stage,script in enumerate(scripts):
   with (d/'logs'/(case+'_'+str(stage)+'.log')).open('x') as log:
    code=subprocess.call([sys.executable,str(script),str(d/case)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   if code:return dict(case=case,stage=stage,exit_code=code)
  return dict(case=case,exit_code=0)
 stages=[]
 with ThreadPoolExecutor(max_workers=3) as pool:
  for future in as_completed([pool.submit(run,c) for c in ['case_01','case_02','case_03']]):
   stages.append(future.result());(d/'stages.json').write_text(json.dumps(stages,indent=2));print('QUALITY TERMINAL',stages[-1],flush=True)
 assert len(stages)==3 and all(s['exit_code']==0 for s in stages)
 results=[]
 with cache.installed():
  for case in ['case_01','case_02','case_03']:
   path=d/case/'verification.json';a=json.loads(path.read_text());assert a['status']=='pass' and a['histogram_rank_topk_mae_checks']==36
   bindings.update(a['bindings']);bindings[str(path)]=sha(path)
   r=json.loads((d/case/'comparison.json').read_text())
   results.append(dict(case=case,metrics=r['metrics'],fixed_comparisons=r['primary_checks'],cold_primary_comparisons=[x for x in r['primary_checks'] if x['label']=='cold']))
  assert all(sha(p)==h for p,h in bindings.items())
  with (d/'research_decision_v1.json').open('x') as stream:
   json.dump(dict(status='all108_terminal_batch_metric_vectors_independently_verified',bindings=bindings,rows=results,all3_cold_primary_fixed_comparison_rule_pass=all(x['pass_primary_gate'] for r in results for x in r['cold_primary_comparisons']),scope='Isolated model batch quality ablation. Exposed3case cohort, primary/supplemental labels unchanged. Model resource/objective improvements do not substitute for forecast or native utility/full-flow gates.'),stream,indent=2)
 print('ALL108 TERMINAL BATCH QUALITY VECTORS VERIFIED',flush=True)

if __name__=='__main__':main()
