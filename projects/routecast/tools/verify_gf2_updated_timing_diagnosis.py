"""Independent report-table arithmetic and retained-state identity checks."""
import json
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_recurrence_updated_timing_diagnosis_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'];assert all(sha(f)==h for f,h in p['inputs_sha256'].items());assert sha(root/'tools/diagnose_gf2_updated_timing.py')==p['source_sha256'];rows=[]
for row in r['rows']:
 w=row['width'];detail=out/f'gf2_d{w}.json';assert sha(detail)==row['detail_sha256'];d=json.loads(detail.read_text());assert sha(root/f'work/gf2_d{w}_updated_native_import_2026-10-06/design.blif')==d['blif_sha256']
 for label,suffix in (('candidate','updated_native_import'),('reference','swapped_place_cold')):
  text=(root/f'work/gf2_d{w}_{suffix}_2026-10-06/report_timing.setup.rpt').read_text();blocks=text.split('\n#Path ')[1:];assert len(blocks)==32
  for block,expected in zip(blocks,d[label+'_paths']):
   assert int(block.splitlines()[0])==expected['rank'];table=block.split('Point ',1)[1].split('data arrival time',1)[0];points=[]
   for line in table.splitlines():
    fields=line.split()
    if len(fields)==4 and fields[1] in ('(.names)','(.input)','(.output)'):points.append((fields[0],fields[1][1:-1],Decimal(fields[2]),Decimal(fields[3])))
   assert points==[(v['point'],v['kind'],Decimal(v['increment_ns']),Decimal(v['cumulative_ns'])) for v in expected['points']]
   total=Decimal(0)
   for name,kind,inc,cumulative in points:
    total+=inc;assert abs(total-cumulative)<=Decimal('.0005')*(len(points)+1)
   assert abs(total-Decimal(expected['arrival_ns']))<=Decimal('.0005')*(len(points)+1)
 original=json.loads((root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}/receipt.json').read_text());updated=json.loads((root/f'experiments/gf2_recurrence_placement_updates_2026-10-06/gf2_d{w}/receipt.json').read_text());affected=set(updated['affected']['affected_net_ids']);old={x['connection_id']:x for x in original['records']};retained=0
 for record in updated['records']:
  if record['net_id'] not in affected:
   assert record==old[record['connection_id']];retained+=1
 # Independently recalculate exact-sequence pairs and sums by table point labels.
 def key(v):return tuple((x['point'],x['kind']) for x in v['points'])
 refs={key(v):v for v in d['reference_paths']};matched=[v for v in d['candidate_paths'] if key(v) in refs];assert len(matched)==row['matched_reported_sequences']==len(d['identical_ordered_point_sequence_pairs'])
 for c,pair in zip(matched,d['identical_ordered_point_sequence_pairs']):
  ref=refs[key(c)];assert c['rank']==pair['candidate_rank'] and ref['rank']==pair['reference_rank'];assert Decimal(pair['arrival_delta_ns'])==Decimal(c['arrival_ns'])-Decimal(ref['arrival_ns']);assert Decimal(pair['logic_delta_ns'])==Decimal(c['logic_ns'])-Decimal(ref['logic_ns']);assert Decimal(pair['interconnect_delta_ns'])==sum(Decimal(v['delta_ns']) for v in pair['edge_deltas'])
 rows.append({'width':w,'reported_paths_verified':64,'retained_connection_records_exactly_unchanged':retained,'exact_sequence_pairs':len(matched)})
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'Independent whitespace timing table parse, Decimal rounded arithmetic, report hash binding, identical-point pairing and full retained prediction-record equality. No hidden omitted-path or unique causal attribution claim.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
