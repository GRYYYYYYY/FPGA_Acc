"""Independent cold-only cohort proof; no candidate artifacts required."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_screened4_baseline_swapped_cold_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==d for f,d in p['inputs'].items());rows=[]
for row,total in zip(r['rows'],[371,1514,5070]):
 n=row['count'];assert row['exit_code']==0 and not row['timed_out'];assert all(sha(f)==d for f,d in row['files'].items());work=out/f'n{n}';graph=Path(row['command'][row['command'].index('--read_rr_graph')+1]);a=audit(graph,work/'design.route');assert len(a['connections'])==total and not a['overflow_units'];text=(work/'cold.log').read_text();assert 'VPR succeeded' in text and 'Completed routing consistency check successfully.' in text;assert row['cpd_ns']==re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1];assert row['wirelength']==int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);rows.append(dict(count=n,connections=total,cold_cpd_ns=row['cpd_ns'],cold_wirelength=row['wirelength'],candidate_cpd_ns=None,candidate_wirelength=None,joint_nonregression=False,descriptive_selection='cold',cold_rrr_iterations=row['rrr_iterations'],cold_route_seconds=row['seconds']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='ALL3 cold-only native/physical evidence without any candidate dependency; own cold canonical and selected ledger proofs follow.'),indent=2)+'\n')
