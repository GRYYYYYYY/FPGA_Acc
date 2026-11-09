"""Original binary FULL/STA zero-fixup and physical identity evidence audit."""
import json
import re
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/loaded_candidate_original_reload_v3_2026-10-06'
parent=ROOT/'experiments/native_loaded_candidate_import_gf2_v3_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and p['parent_receipt_sha256']==sha(parent/'receipt.json')
assert len(r['rows'])==6 and {(x['width'],x['decision']) for x in r['rows']}=={(w,d) for w in (32,64,128) for d in ('A','R')}
def paths(path):return {n:sorted(v) for n,v in physical_paths(path).items() if v}
rows=[]
for row in r['rows']:
    work=out/f"gf2_d{row['width']}_{row['decision']}"
    assert row['exit_code']==0 and row['mismatches']==row['fixups']==0
    assert row['cpd_ns']==row['expected_cpd_ns']
    assert all(sha(path)==h for path,h in row['files'].items())
    cmd=row['command'];assert sha(cmd[0])==p['binary_sha256']=='a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc'
    assert '--analysis' in cmd and '--route' not in cmd and cmd[cmd.index('--check_route')+1]=='full'
    graph=Path(cmd[cmd.index('--read_rr_graph')+1]);assert sha(graph)==row['graph_sha256']
    text=(work/'reload.log').read_text()
    for marker in ('VPR succeeded','RouterOpts.check_route: FULL','Completed routing consistency check successfully.'):assert marker in text
    assert int(re.search(r'Found (\d+) mismatches',text)[1])==0
    assert int(re.search(r'Fixed (\d+) routing traces',text)[1])==0
    assert float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[1])==row['cpd_ns']
    source=parent/work.name/'output.route'
    assert paths(work/'design.route')==paths(source)
    physical=audit(graph,work/'design.route')
    assert physical['overflow_units']==0 and len(physical['connections'])=={32:264,64:491,128:908}[row['width']]
    rows.append(dict(width=row['width'],decision=row['decision'],connections=len(physical['connections']),cpd_ns=row['cpd_ns'],original_FULL_zero_fixups=True,physical_paths_preserved=True))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Six independent original VPR canonical FULL/STA zero-fixup proofs and original RR physical/capacity audits. One-step prescribed decisions, no paired reference gate, owner lifecycle or benefit evidence.'),indent=2)+'\n')
print('verified six original reload bundles',sum(row['connections'] for row in rows),'connections')
