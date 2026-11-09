import json,sys
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_native_demand_bounded_v1_2026-10-08';ref=R/'experiments/aes_native_demand_estimates_v1_2026-10-08';bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
for root in [out,ref]:
 p=root/'receipt.json';d=json.loads(p.read_text());assert all(r['exit_code']==0 for r in d['rows']);assert all(sha(k)==v for k,v in d['bindings'].items());bindings[str(p)]=sha(p)
for name in ['aes_cipher','aes_inv_cipher']:
 w=out/name/'resident';old=ref/name/'resident'
 for file in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  p=old/file;proof=json.loads(p.read_text());assert proof['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(k)==v for k,v in proof['bindings'].items());bindings[str(p)]=sha(p)
 receipts=[]
 for root in [old,w]:
  p=root/'receipt.json';r=json.loads(p.read_text());assert all(sha(k)==v for k,v in r['bindings'].items()) and all(sha(k)==v for k,v in r['files'].items());bindings[str(p)]=sha(p);receipts.append(r)
 for file in ['initial.json','floors.json','sketch.json','round0.json','round1.json']:
  assert json.loads((w/file).read_text())==json.loads((old/file).read_text());bindings[str(w/file)]=sha(w/file);bindings[str(old/file)]=sha(old/file)
 for a,b in zip(receipts[0]['rounds'],receipts[1]['rounds']):assert {k:v for k,v in a.items() if k not in ['seconds','state_file']}=={k:v for k,v in b.items() if k not in ['seconds','state_file']}
 timings=[{k:r[k] for k in ['total_paid_resident_seconds','model_setup_seconds','initial_seconds','feedback_seconds','cpp_search_seconds']} for r in receipts];rows.append({'name':name,'all_paths_floors_budgets_epochs_prices_affected_NETs_events_and_both_ledgers_exact_parity':True,'reference_timing':timings[0],'certified_bound_workspace_delta_timing':timings[1],'scope':'Complete output/event parity to independently audited original model. Single serial observed timings; no stable speed or native/fullworkflow gain claim.'})
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(json.dumps(rows,indent=2))
