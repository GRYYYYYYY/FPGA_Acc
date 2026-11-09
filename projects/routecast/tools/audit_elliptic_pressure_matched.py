"""Authenticated same-cohort pressure-only path/cost comparison."""
import json,argparse
from pathlib import Path
from pre_route_endpoints import sha
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path('experiments/elliptic_atomic_pressure_matched_2026-10-05'));parser.add_argument('--background',type=Path,default=Path('experiments/elliptic_prospective_feedback_2026-10-05/candidate_6_prediction.json'));args=parser.parse_args();root=args.root
p=json.loads((root/'protocol.json').read_text());r=json.loads((root/'receipt.json').read_text())
assert all(sha(f)==h for f,h in p['inputs_sha256'].items())
assert all(sha(root/'source'/f)==h for f,h in p['source_sha256'].items())
background_path=args.background;assert p['inputs_sha256'][str(background_path)]==sha(background_path);background=json.loads(background_path.read_text());base={x['connection_id']:x for x in background['connections']};nets=set(p['selected_nets']);preds={}
for alpha in p['alphas']:
 q=json.loads((root/f'prediction_{alpha}.json').read_text());rows={x['connection_id']:x for x in q['connections']};assert len(rows)==len(q['connections']) and rows.keys()==base.keys()
 for cid,x in rows.items():
  assert all(x[k]==base[cid][k] for k in ('net_id','source','sink'))
  if x['net_id'] not in nets:assert x==base[cid]
 report=json.loads((root/f'report_{alpha}.json').read_text());assert report['report']['net_ids']==sorted(nets);assert report['report']['physical_audit']['all_physical_and_union_checks_passed'];assert report['report']['recomputed_connections']==1225
 assert report['changed_vs_background']==sum(x['physical_edge_ids']!=base[cid]['physical_edge_ids'] for cid,x in rows.items())
 preds[alpha]=rows
changed=[cid for cid in sorted(base) if preds[0][cid]['physical_edge_ids']!=preds[256][cid]['physical_edge_ids']];assert changed==sorted(r['pressure_only_changed_connection_ids'])
scores={x['alpha']:x['scores'] for x in r['reports']};deltas={k:scores[256][k]-scores[0][k] for k in scores[0]}
a={'scope':'same frozen background, same 52 nets/1225 connections and full graph; separates pressure from search replacement','input_and_source_hashes_verified':True,'pressure_only_changed_connections':len(changed),'pressure_only_changed_nets':len({base[c]['net_id'] for c in changed}),'pressure_minus_zero_score_deltas':deltas,'artifact_sha256':{f.name:sha(f) for f in root.iterdir() if f.is_file()},'auditor_sha256':sha(__file__),'limitations':['physical audit does not establish joint-tree legality','development estimate only, no native quality implication']}
(root/'comparison_audit.json').write_text(json.dumps(a,indent=2)+'\n');print(json.dumps({k:v for k,v in a.items() if k!='artifact_sha256'}))
