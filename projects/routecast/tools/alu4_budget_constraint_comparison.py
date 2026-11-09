"""Independent exact-RC paired constraint diagnosis, not policy acceptance."""
import json
from pathlib import Path
from buffered_delay_cost import BufferedDelayCost
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
roots=[Path(f'experiments/alu4_budget_constraint_m{i}_2026-10-05') for i in (1,2)];protocols=[json.loads((p/'protocol.json').read_text()) for p in roots];receipts=[json.loads((p/'receipt.json').read_text()) for p in roots];assert protocols[0]['input_sha256']==protocols[1]['input_sha256'];assert all(sha(p)==h for p,h in protocols[0]['input_sha256'].items());assert all(r['reports'][0]['built']==90 and r['reports'][0]['failure'] is None for r in receipts)
g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');m=BufferedDelayCost(g);old=json.loads(Path('experiments/alu4_incremental_budget_cohort_prepared_2026-10-05/prediction.json').read_text());rows={r['connection_id']:r for r in old['connections']};summaries=[]
for multiplier,root in zip((1,2),roots):
 candidates=json.loads((root/'attempted_paths.json').read_text())[0]['candidate_paths'];slower=[];faster=[]
 for r in candidates:
  b=rows[r['connection_id']];before=m.path_delay(b['source'],b['physical_edge_ids']);after=m.path_delay(r['source'],r['physical_edge_ids']);assert sum(m.weights[a] for a in r['physical_edge_ids'])<=multiplier*sum(m.weights[a] for a in b['physical_edge_ids'])
  if after>before:slower.append(r['connection_id'])
  elif after<before:faster.append(r['connection_id'])
 summaries.append({'multiplier':multiplier,'slower_cids':slower,'faster_cids':faster,'unchanged_delay':90-len(slower)-len(faster),'candidate_scores':receipts[multiplier-1]['reports'][0]['candidate_scores'],'committed_in_diagnostic':receipts[multiplier-1]['reports'][0]['committed']})
r={'summaries':summaries,'input_sha256':protocols[0]['input_sha256'],'receipt_sha256':{str(p/'receipt.json'):sha(p/'receipt.json') for p in roots},'source_sha256':sha(__file__),'scope':'Paired single-net greedy constraint diagnosis; budget2 is not non-increase policy or unseen family proof; 2x arc delay excludes fixed source constant'};(roots[1]/'constraint_comparison.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(summaries),flush=True)
