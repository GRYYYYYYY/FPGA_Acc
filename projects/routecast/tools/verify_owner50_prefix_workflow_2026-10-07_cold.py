"""Independent XML/Fraction snapshots and original reload evidence audit."""
import json
import re
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/owner50_prefix_workflow_2026-10-07_cold'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==len(p['cases'])==12
assert all(sha(f)==h for group in ('sources','binaries') for f,h in p[group].items())
rows=[]
for case,row in zip(p['cases'],r['rows']):
    w=case['width'];assert row['width']==w and row['index']==case['index'] and row['complete'] and row['error'] is None and len(row['rounds'])==1
    assert all(sha(f)==h for f,h in case['inputs'].items())
    for rr in row['rounds']:
        step=rr['step'];work=out/f'mux_w{w}_m{case["index"]}_{step}';snapshot=work/'accepted_state.json'
        assert sha(snapshot)==rr['snapshot_sha256']
        s=json.loads(snapshot.read_text());assert s['revision']==step+1
        ep=json.loads(Path(case['targets'][step]).read_text());assert ep==s['endpoint_metadata']
        native,reload=rr['native'],rr['reload']
        assert all(sha(f)==h for f,h in native['files'].items()) and all(sha(f)==h for f,h in reload['files'].items())
        assert reload['exit_code']==0 and reload['mismatches']==reload['fixups']==0 and reload['cpd_ns']==native['cpd_ns']
        log=(work/'canonical/reload.log').read_text();assert all(t in log for t in ('VPR succeeded','RouterOpts.check_route: FULL','Completed routing consistency check successfully.'))
        template=(ROOT/'tools/verify_tseng_selected_reference_import.py').read_text()
        check=template[template.index('def check('):template.index('inc=json.loads')].replace('1234',str({8:466,16:936,32:1929}[w]))
        tool=out/f'mux_w{w}_m{case["index"]}_{step}_independent_audit.py'
        source="import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(ROOT/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\nfrom native_route_ledger_import import physical_paths\nfrom pre_route_endpoints import sha\n"+f"snapshot=json.loads(Path({str(snapshot)!r}).read_text());ep=snapshot['endpoint_metadata'];graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+f"paths,ledger=check(snapshot,ep)\nassert paths=={{n:sorted(v) for n,v in physical_paths(Path({str(work/'canonical/design.route')!r})).items() if v}}\n"
        tool.write_text(source)
        with tool.with_suffix('.log').open('w') as stream:code=subprocess.run(['python3',str(tool)],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
        assert code==0
    rows.append(dict(width=w,index=case['index'],mode=case['mode'],case_wall_s=row['case_wall_s'],connections_checked={8:466,16:936,32:1929}[w]));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope=p['scope']),indent=2)+'\n')
