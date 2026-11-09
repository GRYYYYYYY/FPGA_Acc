"""Bind all updated-family native proofs and retain negative CPD decisions."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
a=root/'experiments/gf2_recurrence_native_seeded_native_import_2026-10-06';b=root/'experiments/gf2_recurrence_native_seeded_canonical_reload_2026-10-06'
ar=read(a/'receipt.json');br=read(b/'receipt.json');assert ar['all_cases_retained'] and br['all_cases_retained'];assert [x['width'] for x in ar['rows']]==[32,64,128]==[x['width'] for x in br['rows']]
for directory,receipt in ((a,ar),(b,br)):
 protocol=read(directory/'protocol.json');assert receipt['protocol_sha256']==sha(directory/'protocol.json')
 for case,row in zip(protocol['cases'],receipt['rows']):
  hashes=case.get('source_sha256',case.get('sources'));assert all(sha(root/'tools'/n)==h for n,h in hashes.items())
  assert len(row['stages'])==2 and all(s['exit_code']==0 and sha(directory/s['tool'].replace('.py','.log'))==s['log_sha256'] for s in row['stages'])
  for name in ('receipt.json','verification.json'):
   per=root/f"experiments/gf2_d{row['width']}_native_seeded_{'native_import' if directory==a else 'canonical_reload'}_2026-10-06"/name
   assert sha(per)==row[name+'_sha256'] and read(per)==row[name]
assert read(b/'protocol.json')['parent_receipt_sha256']==sha(a/'receipt.json')
rows=[]
for original,canonical in zip(ar['rows'],br['rows']):
 width=original['width'];q=original['receipt.json'];v=original['verification.json'];c=canonical['receipt.json'];cv=canonical['verification.json'];assert cv['receipt_sha256']==canonical['receipt.json_sha256'] and v['receipt_sha256']==original['receipt.json_sha256'];assert c['parent_receipt_sha256']==original['receipt.json_sha256'];assert cv['verified_bundles']==1
 rr=c['results'][0];assert rr['status']=='RELOADED' and rr['sync_fixups']==rr['sync_mismatches']==0 and rr['cpd_ns']==q['cpd_ns']
 ref=root/f'experiments/gf2_d{width}_swapped_place_cold_2026-10-06';refq=read(ref/'receipt.json');refv=read(ref/'verification.json');assert refv['receipt_sha256']==sha(ref/'receipt.json');assert v['reference_cpd_ns']==refq['cpd_ns']
 work=Path(rr['cwd'])/'reload';graph=Path(rr['reload_command'][rr['reload_command'].index('--read_rr_graph')+1]);physical=audit(graph,work/'design.route');assert not physical['overflow_units'] and len(physical['connections'])==q['connections']
 assert all(sha(p)==h for p,h in rr['sha256'].items())
 delta=q['cpd_ns']-refq['cpd_ns'];rows.append({'width':width,'connections':q['connections'],'candidate_cpd_ns':q['cpd_ns'],'same_placement_reference_cpd_ns':refq['cpd_ns'],'candidate_minus_reference_ns':delta,'timing_nonregression_pass':delta<=0,'canonical_FULL_zero_fixup':True,'original_XML_reload_capacity_audit':True,'native_import_receipt_sha256':original['receipt.json_sha256'],'canonical_receipt_sha256':canonical['receipt.json_sha256'],'reference_receipt_sha256':sha(ref/'receipt.json'),'published':False})
out=root/'experiments/gf2_recurrence_native_seeded_quality_2026-10-06';out.mkdir();(out/'verification.json').write_text(json.dumps({'native_aggregate_receipt_sha256':sha(a/'receipt.json'),'canonical_aggregate_receipt_sha256':sha(b/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'All frozen whole-family placement updates validated natively, canonical FULL zero fixups and independent originalXML reload occupancy. Diagnostic timing comparisons only: mixed timing outcomes, no accepted-state publication, speed/quality gain or complete cost claim.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
