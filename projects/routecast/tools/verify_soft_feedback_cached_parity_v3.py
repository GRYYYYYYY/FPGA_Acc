"""Authenticate original independent physical proofs, then compare every frame and event."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/soft_feedback_cached_parity_v3_2026-10-07';out.mkdir();bindings=closure([Path(__file__)]);rows=[]
for name in ['bigkey','dsip','misex3']:
 original=R/f'experiments/mcnc_soft_demand_feedback_v1_2026-10-07/{name}';vp=original/'verification.json';proof=json.loads(vp.read_text());assert proof['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass'];bindings[str(vp)]=sha(vp);bindings.update(proof['bindings']);ref=json.loads((original/'receipt.json').read_text());compared=[]
 for backend,dirname in [('cached_cpp','mcnc_soft_demand_feedback_cached_v3_2026-10-07')]:
  folder=R/f'experiments/{dirname}/{name}';rp=folder/'receipt.json';receipt=json.loads(rp.read_text());bindings.update(receipt['bindings']);bindings.update(receipt['files']);bindings[str(rp)]=sha(rp);assert len(receipt['rounds'])==len(ref['rounds'])==2
  protocol=json.loads((folder/'protocol.json').read_text());original_protocol=json.loads((original/'protocol.json').read_text());assert protocol['rounds']==original_protocol['rounds'] and protocol['price_unit_integer']==original_protocol['price_unit_integer'] and protocol['required_connections']==original_protocol['required_connections'];events=0
  for index,(a,b) in enumerate(zip(ref['rounds'],receipt['rounds'])):
   for key in ['round_index','changed_nodes','affected_nets','events','overflow_before','overflow_after']:assert a[key]==b[key],(name,backend,index,key)
   assert json.loads((original/f'round{index}.json').read_text())==json.loads((folder/f'round{index}.json').read_text());events+=len(a['events'])
  assert json.loads((original/'sketch.json').read_text())==json.loads((folder/'sketch.json').read_text());compared.append(dict(backend=backend,events=events,full_frames=2,paid_feedback_seconds=receipt['total_paid_feedback_seconds'],cpp_search_seconds=receipt.get('cpp_search_seconds')))
 rows.append(dict(name=name,completed=proof['completed'],overflow_units=proof['overflow_units'],comparisons=compared));print('PASS actual frame/event parity',name,proof['events'],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,all_source_proofs_physical_fullquery_budget_epoch_ledger_price_and_frame_event_parity_pass=True,scope='C++ and current Python replay exactly reproduce independently physically audited two-round reference output. Reused existing development native metrics unchanged; no new heldout/native or full-workflow speed evidence.'),indent=2)+'\n')
