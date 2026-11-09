"""All reused ORIGINAL identities against native-captured placement references."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from source_binding import closure
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from rebind_native_seed import rebind
R=Path(__file__).resolve().parents[2];s=R/'experiments/native_resume_nine_update_adder_2026-10-07';o=s/'identity_verification';o.mkdir(exist_ok=False);ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';route=R/'experiments/native_resume_nine_update_adder_step3_workflow_2026-10-07/exchange_canonical/design.route';source=R/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits';sources=closure([Path(__file__)]);inputs={str(p):sha(p) for p in (ep,route,s/'receipt.json')};(o/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,scope='Retrospective independent original-native capture for third placement; all reused tables compared to native references by placement. Excluded from producer clocks on both sides.'),indent=2)+'\n');ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inventory=SharedRRInventory(ctx);seed,proof=rebind(ctx,inventory,ep,route,source,o/'fresh_state3');assert seed.read_bytes()==(s/'rebind_step4/rebound.route').read_bytes()
refs={1:s/'rebind_step2/identity.jsonl',2:R/'experiments/native_resume_cached_identity_adder_2026-10-07/independent_rebind/fresh_native/identity.jsonl',3:o/'fresh_state3/identity.jsonl'}
ref_proofs={1:s/'rebind_step2/receipt.json',2:refs[2].parent/'receipt.json',3:o/'fresh_state3/receipt.json'}
for state,p in ref_proofs.items():
 r=json.loads(p.read_text());assert r['identity_capture_exit_code']==1 and all(sha(f)==h for f,h in r['bindings'].items());inputs[str(p)]=sha(p);inputs[str(refs[state])]=sha(refs[state])
rows=[]
for i in range(2,10):
 p=s/f'rebind_step{i}';r=json.loads((p/'receipt.json').read_text());assert sha(p/'identity.jsonl')==r['identity_table_sha256'];state=(i-2)%3+1;assert (p/'identity.jsonl').read_bytes()==refs[state].read_bytes();inputs[str(p/'receipt.json')]=sha(p/'receipt.json')
 if i>2:
  a=r['identity_relocation'];assert a['native_recapture_performed'] is False and r['identity_capture_exit_code'] is None and all(sha(f)==h for f,h in a['bindings'].items()) and sha(p/'identity.jsonl')==a['output_sha256']
 rows.append(dict(index=i,previous_placement_state=state,native_identity_reference_exact=True,actual_native_recapture=i==2))
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(s/'identity_verification.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,rows=rows,fresh_state3_seed_bytes_exact=True,scope='All original identity tables match actual native capture for the three repeated placements; exact fresh state3 seed and all relocation bindings. Not generic arbitrary-source or concurrency validation.'),indent=2)+'\n');print(rows)
