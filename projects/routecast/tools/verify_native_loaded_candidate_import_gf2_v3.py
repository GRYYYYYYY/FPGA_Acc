"""Independent physical paths, placements and CPD evidence for import frames."""
import json
from pathlib import Path
from pre_route_endpoints import placements, sha
from stream_native_route_audit import audit
from native_route_ledger_import import physical_paths

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/native_loaded_candidate_import_gf2_v3_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==6
def paths(path):return {n:sorted(v) for n,v in physical_paths(path).items() if v}
rows=[]
for spec in p['cases']:
    assert all(sha(path)==h for path,h in spec['inputs'].items())
    width=spec['width'];original=Path(spec['original']);candidate=Path(spec['candidate'])
    for decision in ('A','R'):
        row=next(row for row in r['rows'] if (row['width'],row['decision'])==(width,decision))
        assert row['exit_code']==0 and row['import_marker']
        assert all(sha(path)==h for path,h in row['files'].items())
        assert sha(row['command'][0])==p['binary_sha256'] and sha(row['command'][1])==p['architecture_sha256']
        work=out/f'gf2_d{width}_{decision}';text=(work/'run.log').read_text()
        assert 'VPR succeeded' in text and 'moved candidate passed native FULL routing check' in text
        assert paths(work/'candidate_0.route')==paths(work/'predicted.route')
        for filename in ('candidate_0.route','output.route'):
            result=audit(original/'rr_graph.xml',work/filename)
            assert result['overflow_units']==0 and len(result['connections'])=={32:264,64:491,128:908}[width]
        if decision=='A':
            assert placements(work/'accepted.place',sha(work/'design.net'))==placements(candidate/'design.place',sha(candidate/'design.net'))
            expected=json.loads((candidate.parent.parent/'experiments'/candidate.name/'receipt.json').read_text())['cpd_ns']
        else:
            assert row['restored_marker']
            assert paths(work/'output.route')==paths(work/'seed.route')
            expected=json.loads((ROOT/f'experiments/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}/receipt.json').read_text()).get('cpd_ns')
        if expected is not None:assert row['cpd_ns']==expected
        rows.append(dict(width=width,decision=decision,physical_connections_checked=2*{32:264,64:491,128:908}[width],candidate_paths_exact=True,cpd_ns=row['cpd_ns']))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent physical graph/capacity and captured input path parity, accepted placements and rejected route parity. Internal STA restoration is native assertion evidence, not independent STA replay; original reload pending.'),indent=2)+'\n')
print('verified six loaded import frame cases')
