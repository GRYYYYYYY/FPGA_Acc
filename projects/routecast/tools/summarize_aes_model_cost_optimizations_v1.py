import json,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_model_cost_optimizations_v1_2026-10-08';out.mkdir();bindings={str(Path(__file__)):sha(Path(__file__))};variants={'original':'aes_native_demand_estimates_v1_2026-10-08','delta_ledger':'aes_native_demand_delta_ledger_v1_2026-10-08','direct_index_plus_delta':'aes_native_demand_direct_index_v1_2026-10-08','workspace_plus_delta':'aes_native_demand_workspace_v1_2026-10-08'};rows=[]
for mode,folder in variants.items():
 root=R/'experiments'/folder;receipt=root/'receipt.json';d=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings[str(receipt)]=sha(receipt)
 if mode!='original':
  proof=root/'verification.json';p=json.loads(proof.read_text());assert all(x['all_paths_floors_budgets_epochs_prices_affected_NETs_events_and_both_ledgers_exact_parity'] for x in p['rows']);assert all(sha(k)==v for k,v in p['bindings'].items());bindings[str(proof)]=sha(proof)
 for row in d['rows']:
  assert row['exit_code']==0;file=root/row['name']/'resident/receipt.json';x=json.loads(file.read_text());assert all(sha(k)==v for k,v in x['bindings'].items()) and all(sha(k)==v for k,v in x['files'].items());bindings[str(file)]=sha(file);rows.append({'variant':mode,'name':row['name'],'estimator_process_wall_seconds':row['estimator_process_wall_seconds'],'model_measured_before_receipt_hashing_seconds':x['total_paid_resident_seconds'],'model_setup_seconds':x['model_setup_seconds'],'initial_seconds':x['initial_seconds'],'feedback_seconds':x['feedback_seconds'],'cpp_search_seconds':x['cpp_search_seconds']})
assert all(sha(k)==v for k,v in bindings.items());(out/'comparison.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Same full physical query scope and identical model state/events. Compile excluded; per-process model setup, floors, feedback and outputs included in process clock. Single serial noninterleaved observations; no stable speed ratio, fullnative workflow gain, unseen-family or hardware claim.'},indent=2)+'\n');print(rows)
