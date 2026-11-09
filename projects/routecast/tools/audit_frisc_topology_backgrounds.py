"""Independent complete nine-placement physical and score audit."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from prepared_endpoints import PreparedEndpoints
from physical_prediction_audit import audit
from feedback_scores import scores
root=Path('experiments/frisc_topology_backgrounds_2026-10-05');p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text());assert len(r['rows'])==9 and r['inputs_unchanged']
assert all(sha(f)==h for f,h in p['inputs_sha256'].items());assert all(sha(root/'source'/f)==h for f,h in p['source_sha256'].items());assert p['prospective_protocol_sha256']==sha('experiments/frisc_prospective_protocol_2026-10-05/protocol.json')
e=json.loads(Path('experiments/frisc_endpoints_2026-10-05/endpoints.json').read_text());g=read_rr_graph(e['inputs']['graph']['path']);frontend=PreparedEndpoints(e['inputs']['net']['path'],e['inputs']['graph']['path'],e['inputs']['place']['path']);reports=[]
for cid in range(9):
 after=e if cid==0 else frontend.project(Path(f'experiments/frisc_local_candidates_2026-10-05/candidate_{cid}.place'))[0]
 file=root/('baseline_prediction.json' if cid==0 else f'candidate_{cid}_prediction.json');prediction=json.loads(file.read_text());checked=audit(g,after,prediction);assert scores(g,after,prediction['node_occupancy'])==r['rows'][cid]['scores'];assert r['rows'][cid]['candidate_id']==cid
 reports.append({'candidate_id':cid,'physical_audit':checked,'prediction_sha256':sha(file)})
assert all(sha(f)==h for f,h in p['inputs_sha256'].items())
(root/'independent_audit.json').write_text(json.dumps({'reports':reports,'auditor_sha256':sha(__file__),'receipt_sha256':sha(root/'receipt.json'),'protocol_sha256':sha(root/'protocol.json'),'all_input_and_source_hashes_verified':True},indent=2)+'\n');print(json.dumps({'placements':9,'connections_each':len(e['connections']),'passed':True}))
