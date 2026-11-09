"""Verify complete native outcomes while retaining mux32 nonpublication."""
import json
import re
from pathlib import Path
from pre_route_endpoints import placements,sha
from stream_native_route_audit import audit
from native_route_ledger_import import physical_paths

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_wire_penalty_w8m3_quality_gate_2026-10-07'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==len(p['cases'])==1
assert all(sha(f)==h for group in ('sources','binaries') for f,h in p[group].items())
rows=[]
def paths(path):return {n:sorted(v) for n,v in physical_paths(path).items() if v}
for spec,row in zip(p['cases'],r['rows']):
    width=row['width'];index=spec['index'];assert width==spec['width'] and index==row['index']
    if row['status'] in ('ALLOCATION_NOT_SUBMITTED','INCOMPLETE_NOT_SUBMITTED'):
        assert not (out/f'w{width}_m{index}/run.log').exists();rows.append(dict(width=width,index=index,status=row['status']));continue
    assert row['status']=='RELOADED' and row['error'] is None and row['native_exit_code']==0
    native,reload=row['native'],row['reload'];work=out/f'w{width}_m{index}';graph=Path(spec['source'])/'rr_graph.xml'
    assert all(sha(f)==h for f,h in spec['inputs'].items())
    assert all(sha(f)==h for f,h in native['files'].items()) and all(sha(f)==h for f,h in reload['files'].items())
    text=(work/'run.log').read_text();m=re.search(r'same-target gate predicted_cpd_ns=([0-9.]+) reference_cpd_ns=([0-9.]+) selected=(\w+)',text);assert m
    pred,ref=map(float,m.groups()[:2]);assert m[3]==('reference' if pred>ref else 'predicted')
    assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0 and reload['cpd_ns']==native['cpd_ns'] and abs(reload['cpd_ns']-min(pred,ref))<=5.1e-5
    assert sha(reload['command'][0])=='a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc'
    original=(work/'canonical/reload.log').read_text()
    for marker in ('VPR succeeded','RouterOpts.check_route: FULL','Completed routing consistency check successfully.'):assert marker in original
    assert int(re.search(r'Found (\d+) mismatches',original)[1])==int(re.search(r'Fixed (\d+) routing traces',original)[1])==0
    assert paths(work/'candidate_0.route')==paths(work/'predicted.route') and paths(work/'output.route')==paths(work/'canonical/design.route')
    for name in ('candidate_0.route','loaded_reference.route','canonical/design.route'):
        result=audit(graph,work/name);assert result['overflow_units']==0 and len(result['connections'])=={8:466,16:936,32:1929}[width]
    assert placements(work/'accepted.place',sha(work/'design.net'))==placements(work/'identity_probe/design.place',sha(work/'identity_probe/design.net'))
    rows.append(dict(width=width,index=index,status=row['status'],selected=m[3],predicted_cpd_ns=pred,reference_cpd_ns=ref,original_cpd_ns=reload['cpd_ns'],physical_connections_checked=3*{8:466,16:936,32:1929}[width]))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Three complete candidate/reference/final physical/capacity audits and original FULL/STA zero-fixup proofs. No wholefamily success, timing/generalization/production benefit.'),indent=2)+'\n')
print('verified focused gate, candidate/reference/final physical audits; selection explicit')
