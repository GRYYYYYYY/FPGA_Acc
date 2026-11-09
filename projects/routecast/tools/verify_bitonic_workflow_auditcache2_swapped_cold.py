from native_qor_admission import admit
"""Independent original XML cold audit and fixed-target joint QoR comparison."""
import json,re
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit_cached import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_workflow_auditcache2_swapped_cold_2026-10-07'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==d for f,d in p['inputs'].items());rows=[]
for row,total in zip(r['rows'],[371,1514,5070]):
 n=row['count'];assert row['exit_code']==0 and not row['timed_out'];assert all(sha(f)==d for f,d in row['files'].items());work=out/f'n{n}';graph=Path(row['command'][row['command'].index('--read_rr_graph')+1]);a=audit(graph,work/'design.route');assert len(a['connections'])==total and a['overflow_units']==0
 rawbase=ROOT/'experiments/bitonic_workflow_auditcache2_resident_staging_native_import_2026-10-07';rawreceipt=json.loads((rawbase/'receipt.json').read_text());rawrow=next(x for x in rawreceipt['rows'] if x['count']==n);gate=admit(row,rawrow);cpd=gate['candidate_cpd_ns'];wire=gate['candidate_wirelength']
 if gate['admitted']:
  canonical=ROOT/f'experiments/bitonic_workflow_auditcache2_resident_staging_n{n}_canonical_2026-10-07';v=json.loads((canonical/'verification.json').read_text());cr=json.loads((canonical/'receipt.json').read_text());assert v['receipt_sha256']==sha(canonical/'receipt.json');x=cr['results'][0];assert all(sha(f)==d for f,d in x['sha256'].items());cw=Path(x['cwd'])/'reload';log=(cw/'reload.log').read_text();assert Fraction(cpd)==Fraction(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);assert wire==int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1])
 good=gate['admitted']
 rows.append(dict(count=n,connections=total,cold_cpd_ns=row['cpd_ns'],candidate_cpd_ns=cpd,cold_wirelength=row['wirelength'],candidate_wirelength=wire,joint_nonregression=good,descriptive_selection='candidate' if good else 'cold',cold_rrr_iterations=row['rrr_iterations'],cold_route_seconds=row['seconds']))
 print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='All three fresh same-target cold routes originalXML capacity/path audited; input layouts equal raw candidate bundles; canonical candidate FULL/STA hashes bound. Rounded native log joint comparison only, not an executed acceptance gate or full workflow gain. Serial single observations, prepared inputs.'),indent=2)+'\n')
