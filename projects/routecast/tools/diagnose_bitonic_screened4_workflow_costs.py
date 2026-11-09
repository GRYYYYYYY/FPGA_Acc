"""Disjoint external stage clocks, with direct workflow/cold baseline costs."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_screened4_acceptance_workflow_2026-10-07';r=json.loads((out/'receipt.json').read_text());b=ROOT/'experiments/bitonic_screened4_cold_cost_baseline_2026-10-07';br=json.loads((b/'receipt.json').read_text());final=json.loads((out/'final_evidence.json').read_text());assert r['complete'] and br['complete'];assert final['workflow_seconds']==r['workflow_seconds'] and final['baseline_seconds']==br['baseline_seconds']
def categories(rows):
 result={}
 for row in rows:
  name=row['stage']
  if 'resident_live_staging' in name:k='candidate_frontend_context_seed_staging' if name.startswith('trial') else 'candidate_demand_path_proof'
  elif 'resident_staging_native_import' in name or 'resident_staging_n' in name or 'resident_staging_canonical' in name:k='candidate_native_canonical_validation'
  elif 'selected_state' in name:k='selected_frontend_reload_ledger_proof'
  else:k='cold_reference_route_canonical_proof'
  result[k]=result.get(k,0)+row['seconds']
 assert abs(sum(result.values())-sum(x['seconds'] for x in rows))<1e-9
 return result
w=categories(r['stages']);cold=categories(br['stages']);value=dict(workflow_receipt_sha256=sha(out/'receipt.json'),baseline_receipt_sha256=sha(b/'receipt.json'),final_evidence_sha256=sha(out/'final_evidence.json'),source_sha256=sha(Path(__file__)),workflow_categories_seconds=w,baseline_categories_seconds=cold,workflow_loop_receipt_overhead_seconds=r['workflow_seconds']-sum(w.values()),baseline_loop_receipt_overhead_seconds=br['baseline_seconds']-sum(cold.values()),scope='Disjoint externally measured stages only; do not add inner timings. All costs same pair. Categories describe this implementation, not theoretical bounds or stable speedup. Additional cost diagnosis outside both clocks.')
(out/'cost_breakdown.json').write_text(json.dumps(value,indent=2)+'\n');print(value)
