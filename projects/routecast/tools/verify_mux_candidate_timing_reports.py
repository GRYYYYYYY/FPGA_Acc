"""Audit candidate-specific packing replays and expose worst-path identities."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_candidate_timing_reports_v2_2026-10-06';base=ROOT/'experiments/mux_budget_repair_quality_gate_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');rows=[];bindings={}
def paths(p):return {n:sorted(v)for n,v in physical_paths(p).items()if v}
def first(p):
 t=p.read_text().split('#Path 1\n',1)[1].split('#Path 2',1)[0]
 return dict(startpoint=re.search(r'^Startpoint:\s*(.*)',t,re.M)[1],endpoint=re.search(r'^Endpoint\s*:\s*(.*)',t,re.M)[1],arrival_ns=float(re.search(r'^data arrival time\s+([0-9.]+)',t,re.M)[1]),text=t)
for row in r['rows']:
 w=row['width'];assert row['status']=='ZERO_FIXUP_RELOADED';reload=row['reload'];work=out/f'w{w}';old=ROOT/f'experiments/mux_candidate_timing_reports_2026-10-06/w{w}/canonical/design.net.post_routing'
 assert sha(old)==sha(work/'design.net.post_routing');assert all(sha(p)==h for p,h in reload['files'].items());assert reload['mismatches']==reload['fixups']==0 and reload['exit_code']==0
 assert paths(work/'canonical/design.route')==paths(base/f'w{w}/predicted.route')
 graph=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/rr_graph.xml';a=audit(graph,work/'canonical/design.route');assert a['overflow_units']==0 and len(a['connections'])=={8:466,16:936,32:1929}[w]
 pred=first(work/'canonical/report_timing.setup.rpt');ref=first(base/f'w{w}/canonical/report_timing.setup.rpt')
 rows.append(dict(width=w,original_candidate_cpd_ns=reload['cpd_ns'],candidate_worst_path=pred,reference_worst_path=ref,same_worst_endpoints=pred['startpoint']==ref['startpoint']and pred['endpoint']==ref['endpoint']))
 for p in [old,work/'design.net.post_routing',base/f'w{w}/predicted.route',work/'canonical/report_timing.setup.rpt',base/f'w{w}/canonical/report_timing.setup.rpt']:bindings[str(p)]=sha(p)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,bindings=bindings,scope='3331 original candidate paths preserved and capacity audited; zero-fixup replays after explicitly archived packing synchronization. Top path report 3-decimal precision; endpoint changes preclude direct per-edge causal subtraction.'),indent=2)+'\n');print([(r['width'],r['same_worst_endpoints'])for r in rows])
