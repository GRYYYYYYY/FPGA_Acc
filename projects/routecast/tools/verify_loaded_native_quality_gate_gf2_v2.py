"""Audit same-target selection, imported paths, physical outputs and placements."""
import json
import re
from pathlib import Path
from pre_route_endpoints import sha, placements
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/loaded_native_quality_gate_gf2_v2_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==3
rows=[]
def paths(path):return {n:sorted(v) for n,v in physical_paths(path).items() if v}
for spec,row in zip(p['cases'],r['rows']):
    width=row['width'];assert width==spec['width'] and row['exit_code']==0
    assert all(sha(path)==h for path,h in spec['inputs'].items())
    assert all(sha(path)==h for path,h in row['files'].items())
    assert sha(row['command'][0])==p['binary_sha256'] and sha(row['command'][1])==p['architecture_sha256']
    work=out/f'gf2_d{width}_A';text=(work/'run.log').read_text()
    m=re.search(r'same-target gate predicted_cpd_ns=([0-9.]+) reference_cpd_ns=([0-9.]+) selected=(\w+)',text);assert m
    predicted,reference=map(float,m.groups()[:2]);selected=m[3]
    assert selected==('reference' if predicted>reference else 'predicted')
    cpds=[float(v) for v in re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)]
    assert row['cpd_ns']==cpds[0] # producer binds the printed CPD; report precision is coarser than gate log
    final_cpd=cpds[-1];assert abs(final_cpd-min(predicted,reference))<=5.1e-5
    assert 'VPR succeeded' in text and row['import_marker']
    assert paths(work/'candidate_0.route')==paths(work/'predicted.route')
    graph=Path(row['command'][row['command'].index('--read_rr_graph')+1])
    count={32:264,64:491,128:908}[width]
    for name in ('candidate_0.route','loaded_reference.route','output.route'):
        result=audit(graph,work/name);assert result['overflow_units']==0 and len(result['connections'])==count
    candidate=Path(spec['candidate'])
    assert placements(work/'accepted.place',sha(work/'design.net'))==placements(candidate/'design.place',sha(candidate/'design.net'))
    rows.append(dict(width=width,selected=selected,predicted_cpd_ns=predicted,reference_cpd_ns=reference,cpd_ns=final_cpd,producer_first_report_cpd_ns=row['cpd_ns'],physical_connections_checked=3*count))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent selection arithmetic, input path equality, target placement and original RR capacity/path audit. Original uninstrumented final reload remains required.'),indent=2)+'\n')
print('verified three same-target gates')
