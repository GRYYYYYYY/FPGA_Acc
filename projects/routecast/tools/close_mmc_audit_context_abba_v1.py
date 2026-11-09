"""Full local audit cohort closure, source authentication and bounded interpretation."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from observe_neuron_scaled_present_pipeline_v1 import process
R=Path(__file__).resolve().parents[1]
def main():
 out=R/'experiments/mmc_audit_context_abba_v1_2026-10-17';negative=R/'experiments/mmc_audit_context_modes_negative_v1_2026-10-17/verification.json'
 v=json.loads((out/'verification.json').read_text());n=json.loads(negative.read_text());assert v['all_pass'] and n['all_pass'] and n['both_actual_modes_corrupt_budget_refused'];assert json.loads((out/'terminal.json').read_text())['exit_status']==0
 bindings=dict(v['bindings'])
 for i,row in enumerate(v['results']):
  root=out/f'arm{i}_{row["mode"]}';p=root/'verification.json';a=json.loads(p.read_text());assert sha(p)==row['proof_sha256'] and a['all_pass'] and a['all_proofs_semantically_equal_closed_standalone_audits']
  m=json.loads((out/f'arm{i}_process.json').read_text());assert not process(m['pid'],int(m['start_stat'].rsplit(')',1)[1].split()[19]),m['args']).get('verified_live')
  for section in ['bindings','outputs']:
   for path,digest in a[section].items():assert path not in bindings or bindings[path]==digest;bindings[path]=digest
  for stage in ['initial','sketch','events']:
   assert json.loads((root/(stage+'_context_calls.json')).read_text())==dict(topology=1,electrical=1,scale=1)
   t=json.loads((root/(stage+'_terminal.json')).read_text());assert t['exit_status']==0 and not t['timed_out']
  assert a['fresh_graph_context_loads']==a['fresh_exact_scale_scans']==(1 if row['mode']=='shared' else 3)
  event=json.loads((root/'events_verification.json').read_text());assert event['completed']==115572 and event['events']==96869 and event['overflow_units']==76811
 for p,h in n['bindings'].items():assert p not in bindings or bindings[p]==h;bindings[p]=h
 assert all(sha(p)==h for p,h in bindings.items())
 next_action='Preflight a fresh full fixed-placement MMC workflow variant replacing only the three audit subprocesses with the validated shared-context batch. Preserve fresh RR export, all115572 queries, complete model, identical seed selection/serialization, native and canonical/ignored-pin audits, all costs and original failures. Version the full verifier and stage-accounting expectation before any launch. Do not splice local batch timing into old arm totals or claim net gain from this audit component.'
 result=dict(all_pass=True,all4_arms_original_audits_semantic_parity_and_both_modes_negative_pass=True,connections=115572,events=96869,external_seconds=[x['external_seconds'] for x in v['results']],paired_savings_seconds=[-x['shared_minus_separate_seconds'] for x in v['pairs']],paired_savings_percent=[100*(1-x['shared_over_separate']) for x in v['pairs']],context_builds_per_batch=dict(separate=3,shared=1),interpretation='Observed complete local MMC audit-batch reduction in both registered order-reversed pairs. n2/mode on uncontrolled shared host/cache, not robust general scaling or native continuous workflow benefit. All twelve original audit executions and real inflated-budget negatives pass.',next_action=next_action,bindings=bindings,promoted=False,goal_complete=False)
 for p in [Path(__file__).resolve(),out/'verification.json',out/'terminal.json',negative]:result['bindings'][str(p)]=sha(p)
 path=out/'research_decision_v1.json';assert not path.exists();path.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['external_seconds','paired_savings_seconds','paired_savings_percent','interpretation']},indent=2))
if __name__=='__main__':main()
