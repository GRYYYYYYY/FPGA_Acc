"""Authenticated stage-accounting diagnosis, no fresh speedup claim."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];a=root/'experiments/gf2_continuous_two_updates_v2_2026-10-06';b=root/'experiments/gf2_cold_two_updates_2026-10-06';out=root/'experiments/gf2_continuous_cost_diagnosis_2026-10-06';out.mkdir()
for base in [a,b]:
 v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json')
r=json.loads((a/'receipt.json').read_text());cold=json.loads((b/'receipt.json').read_text());assert r['all_cases_retained'] and cold['all_cases_retained'];rows=[]
for case in r['rows']:
 assert case['complete'] and case['error'] is None;w=case['width'];reference=next(x for x in cold['rows'] if x['width']==w);groups=defaultdict(float)
 for rd in case['rounds']:
  groups['incremental_prediction']+=rd['stage_s'];groups['prepare_and_advance']+=rd['prepare_advance_s']
  for stage in rd['stages']:
   name=stage['tool'];log=a/f"gf2_d{w}_round{rd['round']}_{name}.log";assert sha(log)==stage['log_sha256'] and stage['exit_code']==0
   if name.startswith('verify_') or name=='audit_candidate.py':key='independent_audit_processes'
   elif 'quality_gate' in name:key='quality_selection_process'
   elif 'reference_canonical_reload' in name:key='reference_canonical_reload_process'
   elif 'canonical_reload' in name:key='candidate_canonical_reload_process'
   elif 'native_import' in name:key='candidate_native_routing_process'
   elif 'cold' in name:key='cold_reference_routing_process'
   else:raise ValueError(name)
   groups[key]+=stage['wall_s']
 accounted=case['context_import_s']+sum(groups.values());residual=case['case_wall_s']-accounted;assert residual>=0
 row={'width':w,'groups_s':dict(groups),'context_import_s':case['context_import_s'],'residual_orchestration_serialization_s':residual,'case_wall_s':case['case_wall_s'],'cold_case_wall_s':reference['case_wall_s'],'prediction_share':groups['incremental_prediction']/case['case_wall_s'],'zero_prediction_hypothetical_wall_s':case['case_wall_s']-groups['incremental_prediction'],'zero_prediction_hypothetical_over_cold':(case['case_wall_s']-groups['incremental_prediction'])/reference['case_wall_s']};rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'bindings':{str(base/'receipt.json'):sha(base/'receipt.json') for base in [a,b]},'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'Partition of archived single-run process wall times, not CPU profiler or causal ablation. Groups include child process startup and their internal work. Zero prediction is arithmetic bound with all other stages fixed, not executable policy. Existing unequal acceptance routes/cold policies and setup exclusions preserved; no end-to-end gain.'},indent=2)+'\n')
