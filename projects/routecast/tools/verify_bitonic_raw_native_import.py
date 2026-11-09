"""Raw FULL/STA import binding and descriptive archived-reference comparison."""
import json,re
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_native_candidate_import_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items()) and all(sha(f)==h for f,h in p['binaries'].items());reference=json.loads((ROOT/'experiments/bitonic_native_reference_2026-10-07/verification.json').read_text());rows=[]
for row,ref in zip(r['rows'],reference['rows']):
 n=row['count'];assert n==ref['count'];assert sha(ROOT/f'experiments/bitonic_owner_union_prediction_2026-10-07/n{n}.json')==row['candidate_sha256']
 if n==16:assert row['status']=='INCOMPLETE_NOT_SUBMITTED';rows.append(row);continue
 assert row['status']=='RAW_NATIVE_FULL_STA_SUCCESS' and row['serialized_file_unchanged'] and all(sha(f)==h for f,h in row['files'].items());log=(out/f'n{n}/import.log').read_text();assert 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);assert row['cpd_ns']==re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1];rows.append(dict(count=n,raw_native_success=True,cpd_ns=row['cpd_ns'],reference_cpd_ns=ref['cpd_ns'],cpd_regression=F(row['cpd_ns'])>F(ref['cpd_ns']),wirelength=wire,reference_wirelength=ref['wirelength'],packing_fixups=row['packing_fixups']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Raw native FULL/STA and artifacts bound; archived reference descriptive roundedlog comparison. Packing sync changes occurred, zero-fixup canonical and selectedpath proof pending. Not actualfreshjoint quality gate/accepted benefit.'),indent=2)+'\n');print(rows)
