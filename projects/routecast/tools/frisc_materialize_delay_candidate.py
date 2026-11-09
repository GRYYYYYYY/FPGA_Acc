"""Archive rejected span-gate candidate for native tradeoff evaluation only."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from net_union_commit_gate import check
from physical_prediction_audit import audit
from feedback_scores import scores
out=Path('experiments/frisc_delay_primary_net49_candidate_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'before':'experiments/frisc_shared_trunk_gated_candidate_2026-10-05/prediction.json','paths':'experiments/frisc_delay_guard_net49_2026-10-05/attempted_paths.json','receipt':'experiments/frisc_delay_guard_net49_2026-10-05/receipt.json','graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json'};inputs={p:sha(p) for p in files.values()};g=read_rr_graph(files['graph']);p=json.loads(Path(files['before']).read_text());attempt=json.loads(Path(files['paths']).read_text());assert len(attempt)==1 and attempt[0]['net']==49;staged=attempt[0]['candidate_paths'];assert len(staged)==104;gate=check(g,p,staged);assert gate['accepted'];replacement={r['connection_id']:r for r in staged};rows=[replacement.get(r['connection_id'],r) for r in p['connections']];users={}
for r in rows:
 nodes={r['source']}|{g.edges[e].sink for e in r['physical_edge_ids']}
 users.setdefault(r['net_id'],set()).update(nodes)
demand=Counter(n for nodes in users.values() for n in nodes);pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in demand.items()},'methods':dict(Counter(r['method'] for r in rows)),'requested':len(rows),'completed':len(rows)};e=json.loads(Path(files['endpoints']).read_text());checked=audit(g,e,pred);score=scores(g,e,pred['node_occupancy']);assert score['channel_net_span_sum']==46162 and score['predicted_channel_overuse_units']==0;assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'prediction.json').write_text(json.dumps(pred)+'\n');(out/'source.py').write_text(Path(__file__).read_text());(out/'receipt.json').write_text(json.dumps({'input_sha256':inputs,'physical_audit':checked,'whole_net_gate':gate,'scores':score,'source_sha256':sha(out/'source.py'),'prediction_sha256':sha(out/'prediction.json'),'scope':'candidate rejected by frozen span-improvement policy, explicitly retained as native tradeoff control; not selected or deployed'},indent=2)+'\n')
