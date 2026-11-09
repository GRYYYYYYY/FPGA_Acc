"""Archived-evidence owner two-update integration; not fresh native total cost."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from certified_accepted_route_state import CertifiedAcceptedRouteState
root=Path(__file__).resolve().parents[1];base=root/'experiments/validated_bundle_certificate_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/certified_owner_updates_2026-10-06';out.mkdir();rows=[]
(out/'protocol.json').write_text(json.dumps({'certificate_receipt_sha256':sha(base/'receipt.json'),'sources':{n:sha(root/'tools'/n) for n in ['certified_accepted_route_state.py','validated_bundle_certificate.py','accepted_route_state.py','trial_certified_owner_updates.py']},'scope':'Archived12bundles,3owners each2updates; no native rerun or complete pipeline cost.'},indent=2)+'\n')
for w in [32,64,128]:
 original=root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}/endpoints.json';ctx=PersistentRCContext(original);owner=CertifiedAcceptedRouteState(import_native_ledger(ctx,root/f'work/gf2_d{w}_fixed_original_cold_2026-10-06/design.route'))
 for rd in [0,1]:
  alt={}
  for i,c in enumerate(p['cases']):
   if c['width']!=w or c['round']!=rd:continue
   label='reference' if 'reference_canonical' in c['parent'] else 'predicted';cp=base/str(i)/'certificate.json';alt[label]={'certificate':str(cp),'bundle':str(cp.parent),'certificate_sha256':r['rows'][i]['certificate_sha256']}
  target=root/f'experiments/gf2_d{w}_placement_swap_2026-10-06/endpoints.json' if rd==0 else original;token=owner.token();t=time.monotonic();prepared=owner.prepare_certified(target,alt,token);elapsed=time.monotonic()-t;assert owner.token()==token
  old=json.loads((root/f'work/gf2_continuous_two_updates_v2_2026-10-06/gf2_d{w}/{rd}/experiments/gf2_d{w}_{"native_seeded" if rd==0 else "selected_reverse"}_quality_gate_2026-10-06/selection.json').read_text());assert all(prepared['selection'][k]==old[k] for k in ['selected','selected_cpd_ns','reference_cpd_ns','predicted_cpd_ns'])
  owner.advance(prepared)
  try:owner.advance(prepared)
  except ValueError:stale=True
  else:raise AssertionError('stale commit accepted')
  archived=json.loads((root/f'experiments/gf2_continuous_two_updates_v2_2026-10-06/gf2_d{w}_accepted{rd+1}.json').read_text());records=[owner.state.records[k] for k in sorted(owner.state.records)];assert json.loads(json.dumps(records))==archived['records'];assert {str(k):v for k,v in owner.state.ledger.items()}==archived['ledger']
  row={'width':w,'round':rd,'revision':owner.revision,'prepare_s':elapsed,'selection':prepared['selection'],'stale_commit_rejected':stale,'archived_records_and_ledger_exact':True};rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'complete':len(rows)==6},indent=2)+'\n')
