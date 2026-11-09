"""Audit completed frozen candidate matrix; never infers completion from partial files."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from prepared_endpoints import PreparedEndpoints
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from feedback_scores import scores
from affected_connections import affected
root=Path('experiments/elliptic_pressure_candidate_matrix_2026-10-05');p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text())
assert all(sha(f)==h for f,h in p['inputs_sha256'].items());assert all(sha(root/'source'/f)==h for f,h in p['source_sha256'].items())
ep=json.loads(Path('experiments/elliptic_endpoints_2026-10-04/endpoints.json').read_text());g=read_rr_graph(ep['inputs']['graph']['path']);frontend=PreparedEndpoints(ep['inputs']['net']['path'],ep['inputs']['graph']['path'],ep['inputs']['place']['path']);endpoints={0:ep}
for cid in range(1,9):endpoints[cid],_=frontend.project(Path(f'experiments/elliptic_local_candidates_2026-10-05/candidate_{cid}.place'))
common=set()
for cid in range(1,9):common.update(affected(ep,endpoints[cid])['affected_net_ids'])
while True:
 sources={x['source'] for e in endpoints.values() for x in e['connections'] if x['net_id'] in common}
 expanded=common|{x['net_id'] for e in endpoints.values() for x in e['connections'] if x['source'] in sources}
 if expanded==common:break
 common=expanded
assert sorted(common)==p['common_net_ids']
assert len(r['reports'])==18;seen=set();net_ids=p['common_net_ids'];summaries=[]
for row in r['reports']:
 cid=row['candidate_id'];alpha=row['alpha'];assert (cid,alpha) not in seen;seen.add((cid,alpha))
 report=json.loads((root/f'report_{cid}_{alpha}.json').read_text());assert report==row and report['report']['net_ids']==net_ids
 prediction=json.loads((root/f'prediction_{cid}_{alpha}.json').read_text());bgpath=Path('experiments/elliptic_sketch_neighborhood_2026-10-05/baseline_prediction.json') if cid==0 else Path(f'experiments/elliptic_prospective_feedback_2026-10-05/candidate_{cid}_prediction.json')
 assert p['inputs_sha256'][str(bgpath)]==sha(bgpath);bg=json.loads(bgpath.read_text());b={x['connection_id']:x for x in bg['connections']};q={x['connection_id']:x for x in prediction['connections']}
 assert len(q)==len(prediction['connections']) and q.keys()==b.keys()
 for connection,x in q.items():
  assert all(x[k]==b[connection][k] for k in ('net_id','source','sink'))
  if x['net_id'] not in net_ids:assert x==b[connection]
 assert report['report']['recomputed_connections']==sum(x['net_id'] in net_ids for x in b.values())
 checked=audit(g,endpoints[cid],prediction);assert checked==report['report']['physical_audit'];assert scores(g,endpoints[cid],prediction['node_occupancy'])==report['scores']
 summaries.append({'candidate_id':cid,'alpha':alpha,'changed_connections':sum(x['physical_edge_ids']!=b[c]['physical_edge_ids'] for c,x in q.items())})
assert seen=={(c,a) for c in range(9) for a in (0,256)}
rank={str(a):[x['candidate_id'] for x in sorted((x for x in r['reports'] if x['alpha']==a),key=lambda x:(x['scores']['channel_net_span_sum'],x['scores']['predicted_channel_overuse_units'],x['candidate_id']))] for a in (0,256)};assert rank==r['ranking']
audit={'scope':'complete 18-arm independent physical path/occupancy/score/cohort/hash/nonselected-state/ranking audit','reports':summaries,'ranking':rank,'auditor_sha256':sha(__file__),'artifact_sha256':{f.name:sha(f) for f in root.iterdir() if f.is_file()}}
(root/'matrix_audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({'ranking':rank}))
