"""Original XML/Fraction path/NET-ledger audits, including partial failure state."""
import json
import subprocess
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_joint_budget_reroute_2026-10-06'
base=ROOT/'experiments/mux_live_placement_updates_2026-10-06'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==len(p['cases'])==12
rows=[]
for spec,row in zip(p['cases'],r['rows']):
    width=spec['width'];index=spec['index'];assert width==row['width'] and index==row['index']
    if row['status']=='ALLOCATION_NOT_SUBMITTED':
        rows.append(dict(width=width,index=index,status=row['status']));continue
    assert all(sha(f)==h for f,h in spec['inputs'].items())
    work=out/f'w{width}_m{index}';prediction=work/'prediction.json';assert sha(prediction)==row['prediction_sha256']
    candidate=json.loads(prediction.read_text());assert candidate['completed_connections']==row['completed']
    template=(ROOT/'tools/verify_tseng_selected_reference_import.py').read_text()
    check=template[template.index('def check('):template.index('inc=json.loads')]
    if row['failure'] is None:check=check.replace('1234',str(row['required']))
    else:
        old="assert len(snapshot['records'])==len(queries)==1234 and {q['connection_id'] for q in snapshot['records']}==set(queries)"
        assert old in check
        check=check.replace(old,f"assert len(snapshot['records'])=={row['completed']} and {{q['connection_id'] for q in snapshot['records']}}<=set(queries)")
        assert candidate['status']=='INCOMPLETE_NOT_PUBLISHABLE'
        assert candidate['failure']==row['failure']
    source="import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(ROOT/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\nfrom pre_route_endpoints import sha\n"+f"snapshot=json.loads(Path({str(prediction)!r}).read_text());ep=json.loads(Path({spec['target']!r}).read_text());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+"check(snapshot,ep)\n"
    tool=out/f'w{width}_m{index}_independent_audit.py';tool.write_text(source)
    with tool.with_suffix('.log').open('w') as stream:code=subprocess.run(['python3',str(tool)],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
    assert code==0
    rows.append(dict(width=width,index=index,paths_checked=row['completed'],complete=row['failure'] is None,failure=row['failure']))
    print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Original XML/Fraction endpoint/arc delay/parent/NET union capacity audit. All three outcomes retained; partial states not publishable. No native FULL/STA at moved placement.'),indent=2)+'\n')
