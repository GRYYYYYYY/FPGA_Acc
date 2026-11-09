"""Normalize archived JSON paths; original in-memory tuple/list counter was invalid."""
import json
from pathlib import Path
from pre_route_endpoints import sha
out=Path('experiments/elliptic_neighborhood_recompute_2026-10-05');p=json.loads((out/'protocol.json').read_text())
assert all(sha(f)==h for f,h in p['inputs_sha256'].items())
assert all(sha(out/'source'/f)==h for f,h in p['source_sha256'].items())
refpath=Path('experiments/elliptic_prospective_feedback_2026-10-05/candidate_6_prediction.json');ref=json.loads(refpath.read_text());index={r['connection_id']:r for r in ref['connections']};reports=[]
for hops in (0,1,2):
 file=out/f'prediction_{hops}.json';a=json.loads(file.read_text());rows={r['connection_id']:r for r in a['connections']};assert rows.keys()==index.keys()
 changed=[cid for cid,r in rows.items() if r['physical_edge_ids']!=index[cid]['physical_edge_ids']]
 assert a['node_occupancy']==ref['node_occupancy']
 reports.append({'hops':hops,'normalized_path_differences':len(changed),'same_occupancy':True,'prediction_sha256':sha(file)})
receipt={'execution_session':3981,'exit_code':0,'auditor_sha256':sha(__file__),'protocol_sha256':sha(out/'protocol.json'),'original_receipt_sha256':sha(out/'receipt.json'),'reference_sha256':sha(refpath),'reports':reports,'correction':'Original receipt path_differences_vs_frozen_candidate compared tuples with JSON lists and is invalid; normalized archive comparisons here supersede those counts. Original source/output preserved; maintained driver fixed.'}
(out/'normalized_path_audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(reports))
