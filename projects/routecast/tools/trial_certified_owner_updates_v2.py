"""Archived-evidence owner two-update integration; not fresh native total cost."""
import json,time,shutil
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from certified_accepted_route_state import CertifiedAcceptedRouteState
root=Path(__file__).resolve().parents[1];base=root/'experiments/validated_bundle_certificate_2026-10-06';p=json.loads((base/'protocol.json').read_text());r=json.loads((base/'receipt.json').read_text());v=json.loads((base/'verification.json').read_text());assert v['receipt_sha256']==sha(base/'receipt.json');out=root/'experiments/certified_owner_updates_v2_2026-10-06';out.mkdir();rows=[]
(out/'protocol.json').write_text(json.dumps({'certificate_receipt_sha256':sha(base/'receipt.json'),'sources':{n:sha(root/'tools'/n) for n in ['certified_accepted_route_state.py','validated_bundle_certificate.py','accepted_route_state.py','trial_certified_owner_updates_v2.py']},'scope':'Archived12bundles,3owners each2updates; no native rerun or complete pipeline cost.'},indent=2)+'\n')
for w in [32,64,128]:
 original=root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}/endpoints.json';ctx=PersistentRCContext(original);owner=CertifiedAcceptedRouteState(import_native_ledger(ctx,root/f'work/gf2_d{w}_fixed_original_cold_2026-10-06/design.route'))
 for rd in [0,1]:
  alt={}
  for i,c in enumerate(p['cases']):
   if c['width']!=w or c['round']!=rd:continue
   label='reference' if 'reference_canonical' in c['parent'] else 'predicted';src=base/str(i);dest=out/f'w{w}_round{rd}_{label}';dest.mkdir();
   for name in ['certificate.json','design.blif','design.net','design.place','design.route']:shutil.copyfile(src/name,dest/name)
   cp=dest/'certificate.json';alt[label]={'certificate':str(cp),'bundle':str(cp.parent),'certificate_sha256':r['rows'][i]['certificate_sha256']}
  target=root/f'experiments/gf2_d{w}_placement_swap_2026-10-06/endpoints.json' if rd==0 else original;token=owner.token();t=time.monotonic();prepared=owner.prepare_certified(target,alt,token);elapsed=time.monotonic()-t;assert owner.token()==token
  old=json.loads((root/f'work/gf2_continuous_two_updates_v2_2026-10-06/gf2_d{w}/{rd}/experiments/gf2_d{w}_{"native_seeded" if rd==0 else "selected_reverse"}_quality_gate_2026-10-06/selection.json').read_text());assert all(prepared['selection'][k]==old[k] for k in ['selected','selected_cpd_ns','reference_cpd_ns','predicted_cpd_ns'])
  rejections=[]
  selected=alt[prepared['selection']['selected']]
  for file in [Path(selected['bundle'])/'design.route',Path(selected['certificate'])]:
   content=file.read_bytes();file.write_bytes(content+b'\n')
   try:owner.advance(prepared)
   except ValueError:rejections.append(file.name)
   else:raise AssertionError('changed evidence accepted')
   finally:file.write_bytes(content)
   assert owner.token()==token
  cpd=prepared['selection']['selected_cpd_ns'];prepared['selection']['selected_cpd_ns']=cpd+1
  try:owner.advance(prepared)
  except ValueError:rejections.append('selection')
  else:raise AssertionError('modified selection accepted')
  prepared['selection']['selected_cpd_ns']=cpd;assert owner.token()==token
  owner.advance(prepared)
  try:owner.advance(prepared)
  except ValueError:stale=True
  else:raise AssertionError('stale commit accepted')
  archived=json.loads((root/f'experiments/gf2_continuous_two_updates_v2_2026-10-06/gf2_d{w}_accepted{rd+1}.json').read_text());records=[owner.state.records[k] for k in sorted(owner.state.records)];assert json.loads(json.dumps(records))==archived['records'];assert {str(k):v for k,v in owner.state.ledger.items()}==archived['ledger']
  snapshot=out/f'gf2_d{w}_accepted{rd+1}.json';snapshot.write_text(json.dumps({'revision':owner.revision,'records':records,'ledger':dict(owner.state.ledger),'scale':ctx.rc.scale,'endpoint_metadata':ctx.endpoint_metadata},indent=2)+'\n')
  row={'snapshot_sha256':sha(snapshot),'mutation_rejections':rejections,'alternatives':alt,'width':w,'round':rd,'revision':owner.revision,'prepare_s':elapsed,'selection':prepared['selection'],'stale_commit_rejected':stale,'archived_records_and_ledger_exact':True};rows.append(row);print(row,flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'complete':len(rows)==6},indent=2)+'\n')
