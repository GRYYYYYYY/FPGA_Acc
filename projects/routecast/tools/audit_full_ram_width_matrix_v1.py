"""Physical branch/switch/capacity audit for both predeclared width outcomes."""
import hashlib,json
from pathlib import Path
from stream_native_route_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments'
B=E/'full_ram_width_matrix_v1_2026-10-09';D=E/'full_ram_width_matrix_audit_v1_2026-10-09';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text())
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
assert [row['width'] for row in r['results']]==[192,256]
bindings={str(p):sha(p) for p in [Path(__file__),B/'receipt.json',R/'tools/stream_native_route_audit.py',R/'tools/audit_native_route.py']}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All printed native branches and RR arc/switch identities, per-net unique node capacities, both frozen widths. Not full pin/nonconfigurable legality, Full HDL equivalence, unseen family or net benefit.'),indent=2)+'\n')
rows=[]
for row in r['results']:
    folder=B/f"cw{row['width']}";assert row['exit_code']==0
    result=audit(folder/'rr_graph.xml',folder/'design.route')
    assert result['overflow_units']==0 and result['all_printed_branch_arc_switch_and_union_checks_pass']
    (D/f"cw{row['width']}.json").write_text(json.dumps(result,indent=2)+'\n')
    summary={k:v for k,v in result.items() if k not in ('connections','node_occupancy')}
    summary['width']=row['width'];summary['connection_count']=len(result['connections']);rows.append(summary)
    print(row['width'],result['overflow_units'],len(result['connections']),flush=True)
(D/'verification.json').write_text(json.dumps(dict(passed=True,bindings=bindings,results=rows,admitted_for_prediction=False,
    files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n')
