"""Original XML/Fraction selected snapshot proof and disjoint timer audit."""
import json,subprocess,sys
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_native_acceptance_cost_2026-10-07';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==2;rows=[]
for case,row in zip(p['cases'],r['rows']):
 assert row['index']==case['index'] and row['width']==8;assert all(sha(f)==h for f,h in case['sources'].items());base=ROOT/'experiments'/case['output'];assert row['gate_receipt_sha256']==sha(base/'receipt.json') and row['gate_verification_sha256']==sha(base/'verification.json')
 assert all(x>=0 for x in row['phases_seconds'].values()) and sum(row['phases_seconds'].values())<=row['total_wall_seconds']
 snapshot=out/f"w8_m{row['index']}_accepted_state.json";route=Path(row['selected_route']);assert sha(snapshot)==row['snapshot_sha256'] and sha(route)==row['selected_route_sha256']
 template=(ROOT/'tools/verify_tseng_selected_reference_import.py').read_text();check=template[template.index('def check('):template.index('inc=json.loads')].replace('1234','466');tool=out/f"w8_m{row['index']}_independent_snapshot.py"
 source="import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(ROOT/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\nfrom native_route_ledger_import import physical_paths\n"+f"snapshot=json.loads(Path({str(snapshot)!r}).read_text());ep=snapshot['endpoint_metadata'];graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+f"paths,ledger=check(snapshot,ep)\nassert paths=={{n:sorted(v) for n,v in physical_paths(Path({str(route)!r})).items() if v}}\n"
 tool.write_text(source)
 with tool.with_suffix('.log').open('w') as stream:code=subprocess.run([sys.executable,str(tool)],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0;rows.append(dict(index=row['index'],connections=466,total_wall_seconds=row['total_wall_seconds'],snapshot_sha256=sha(snapshot)));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Disjoint measured phases checked and both imported selected snapshots independently originalXML Fraction/tree/capacity/ledger/NET-name route checked. Separate proof runtime excluded from reported native acceptance timers; estimator/input prep/fallback remain unmeasured in this study. No end-to-end speed claim.'),indent=2)+'\n')
