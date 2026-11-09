"""Preserve all earlier binding records and cover reported output endpoints."""
import sys,json,hashlib
from pathlib import Path
from native_STA_task_binding_v3 import make_binder as old
from native_STA_task_binding_v4 import make_binder as new
P=Path('work/native_joint_budget_net_repair_v2_20261016');cases=json.load(open(P/'protocol.json'))['cases'];results=[];inputs=[Path(__file__),Path('tools/native_STA_task_binding_v4.py'),Path('tools/native_STA_task_binding_v3.py'),Path('tools/native_setup_path_parser.py'),P/'protocol.json']
for c in cases:
    report=P/c['label']/'initial/native_validation/report_timing.setup.rpt'
    a=old(c['native_case'],c['connections'])(report,0);b=new(c['native_case'],c['connections'])(report,0)
    assert [r for r in b['arcs'] if r['sink_kind']!='output']==a['arcs']
    pads=[r for r in b['arcs'] if r['sink_kind']=='output'];expected=sum('.outpad[' in p['endpoint'] for p in b['paths']);assert len(pads)==expected
    assert all(not r['intracluster'] and 'task' in r for r in pads)
    results.append(dict(case=c['label'],prior_arcs_preserved=len(a['arcs']),output_pad_arcs_bound=len(pads),reported_output_endpoints=expected))
    inputs.extend([report,Path(c['connections']),*[Path(c['native_case'])/f for f in ['circuit.blif','circuit.net','circuit.place','rr_graph.xml']]])
D=Path('work/native_STA_output_binding_checks_20261016');D.mkdir(exist_ok=False)
(D/'audit.json').write_text(json.dumps(dict(status='three_reports_prior_bindings_preserved_all_reported_output_pad_arcs_bound',cases=results,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},scope='Zero threshold coverage check only; packed wiring/netlist outputs/root pin class/placement match unique RR task. No rerouting, arbitrary nonzero-period SDC or policy adoption. Frozen v2 runs unchanged.',research_complete=False),indent=2)+'\n');print(json.dumps(results))
