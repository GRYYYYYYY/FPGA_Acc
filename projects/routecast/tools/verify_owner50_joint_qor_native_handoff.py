"""Independent selected-state XML/Fraction/NET-tree and admission checks."""
import json,subprocess,sys
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_joint_qor_native_handoff_2026-10-07';cold=ROOT/'experiments/mux_joint_qor_cost_cold_reference_2026-10-07'
p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and len(r['rows'])==12
assert all(sha(f)==h for f,h in p['sources'].items()) and all(sha(f)==h for f,h in r['bindings'].items())
cases=json.loads((cold/'protocol.json').read_text())['cases'];rows=[]
for case,row in zip(cases,r['rows']):
 w,i=case['width'],case['index'];assert (row['width'],row['index'])==(w,i);work=out/f'w{w}_m{i}';snapshot=work/'accepted_state.json';selected=Path(row['selected_route']);assert sha(selected)==row['selected_route_sha256'] and sha(snapshot)==row['snapshot_sha256']
 c,ref=row['candidate_metrics'],row['reference_metrics'];qualifies=c is not None and Fraction(c['cpd_ns'])<=Fraction(ref['cpd_ns']) and c['wirelength']<=ref['wirelength'];assert row['decision']['selected']==('candidate' if qualifies else 'reference')
 if qualifies:assert row['prediction_status']=='ACTUAL_MODEL_PASS_NATIVE_PENDING'
 s=json.loads(snapshot.read_text());ep=json.loads(Path(case['targets'][0]).read_text());assert ep==s['endpoint_metadata'];assert s['revision']==1 and len(s['records'])==row['connections']=={8:466,16:936,32:1929}[w]
 template=(ROOT/'tools/verify_tseng_selected_reference_import.py').read_text();check=template[template.index('def check('):template.index('inc=json.loads')].replace('1234',str(row['connections']))
 tool=work/'independent_selected_state.py'
 source="import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(ROOT/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\nfrom native_route_ledger_import import physical_paths\n"+f"snapshot=json.loads(Path({str(snapshot)!r}).read_text());ep=snapshot['endpoint_metadata'];graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+f"paths,ledger=check(snapshot,ep)\nassert paths=={{n:sorted(v) for n,v in physical_paths(Path({str(selected)!r})).items() if v}}\n"
 tool.write_text(source)
 with (work/'independent_selected_state.log').open('w') as stream:code=subprocess.run([sys.executable,str(tool)],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0
 rows.append(dict(width=w,index=i,selected=row['decision']['selected'],connections=row['connections'],snapshot_sha256=sha(snapshot),audit_sha256=sha(tool)))
 print(w,i,'selected state independently verified',flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='All12 admission choices independently recomputed; all selected snapshot endpoints, originalXML Fraction path delays, uniqueNET-tree parents, capacity and ledgers checked and exact NET-name physical paths equal bound selected native canonical route. Source native FULLSTA proofs authenticated in replay receipts. Archived candidate content replay; not live accepted lifecycle timing, continuous moves or durable publication.'),indent=2)+'\n')
