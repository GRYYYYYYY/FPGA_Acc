"""Independently check isolated capture output and bound actual native artifacts."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_capture_evidence_contract_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and p['source_sha256']==sha(root/'tools/native_capture_evidence.py')
assert r['original_inputs_unchanged'] and all(sha(f)==h for f,h in r['original_input_bindings'].items())
expected={'candidate-wrong-graph','candidate-wrong-terminal-count','candidate-existing-destination','reference-wrong-graph','reference-wrong-terminal-count','reference-existing-destination','uncaptured-native-producer','copy-failure-no-partial-directory','changed-capture-no-output'};assert set(r['checks'])==expected and len(r['checks'])==9
assert not (out/'copy_failure').exists() and not (out/'changed_capture').exists() and not list(out.glob('.capture-*'))
rows=[]
for row,case in zip(r['cases'],p['cases']):
 assert row['name']==case['name'];directory=out/row['name'];manifest=directory/'manifest.json';assert sha(manifest)==row['manifest_sha256'];m=json.loads(manifest.read_text());assert m['source_sha256']==p['source_sha256'] and m['receipt_sha256']==row['receipt_sha256']==sha(case['receipt']) and m['connections']==1234
 assert all(sha(f)==h for f,h in m['source_bindings'].items())
 q=json.loads(Path(case['receipt']).read_text());assert q['cpd_ns']==m['cpd_ns']
 for name,h in m['files_sha256'].items():
  source=Path(case['cwd'])/(case['log'] if name=='capture.log' else name);assert sha(directory/name)==sha(source)==h==q['files_sha256'][str(source)]
 graph=root/'work/nonzero_rc_tseng_reference128_2026-10-06/rr_graph.xml';assert sha(graph)==m['graph_sha256']
 before=audit(graph,directory/'before_sync.route');after=audit(graph,directory/'after_sync.route');assert len(before['connections'])==len(after['connections'])==1234 and before['overflow_units']==after['overflow_units']==0 and before['node_occupancy']==after['node_occupancy']
 rows.append({'name':row['name'],'captured_files_exact':True,'connections':1234,'overflow_units':0,'occupancy_preserved':True})
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'contract_driver_sha256':sha(root/'tools/trial_native_capture_evidence_contract.py'),'cases':rows,'negative_contracts':r['checks'],'scope':'Staged bytes and originalXML physical branch/capacity/occupancy independently checked. Negative/cleanup cases asserted by executed trial; original native inputs unchanged. Does not claim final canonical quality, concurrency/durable transaction or performance.'},indent=2)+'\n');print('verified two byte-exact staged capture bundles,2468 sinks and9 refusal/cleanup contracts')
