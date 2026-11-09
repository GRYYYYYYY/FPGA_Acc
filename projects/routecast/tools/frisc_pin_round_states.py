"""Canonical path-state equality across archived rounds, not convergence inference."""
import argparse,json,hashlib
from pathlib import Path
from pre_route_endpoints import sha
p=argparse.ArgumentParser();p.add_argument('experiments',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);a=p.parse_args();seen={};reports=[];previous=None
for root in a.experiments:
 receipt=json.loads((root/'receipt.json').read_text());file=root/'prediction.json';assert sha(file)==receipt['prediction_sha256'];prediction=json.loads(file.read_text());rows=sorted(prediction['connections'],key=lambda r:r['connection_id']);canonical=[[r['connection_id'],r['net_id'],r['source'],r['sink'],r['physical_edge_ids']] for r in rows];digest=hashlib.sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest();state={r['connection_id']:r['physical_edge_ids'] for r in rows}
 changed=None if previous is None else sum(state[c]!=previous[c] for c in state)
 reports.append({'experiment':str(root),'state_sha256':digest,'repeated_prior_experiment':seen.get(digest),'changed_paths':changed,'scores':receipt['scores_after'],'full_wall_s':receipt['full_wall_s'],'receipt_sha256':sha(root/'receipt.json')});seen.setdefault(digest,str(root));previous=state
report={'rounds':reports,'tool_sha256':sha(__file__),'scope':'observed archived state equality and scores; no infinite-run convergence or native QoR proof'};a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(reports))
