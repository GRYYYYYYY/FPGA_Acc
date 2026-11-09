"""Independent whole-net and channel-score decision for a pin candidate."""
import argparse,json
from pathlib import Path
from rr_graph import read_rr_graph
from net_union_commit_gate import check
from pre_route_endpoints import sha
p=argparse.ArgumentParser();p.add_argument('candidate_dir',type=Path);args=p.parse_args();out=args.candidate_dir
bgpath=Path('experiments/alu4_transfer_2026-10-05/prediction.json');bg=json.loads(bgpath.read_text());pred=json.loads((out/'prediction.json').read_text());old={r['connection_id']:r for r in bg['connections']};changed=[r for r in pred['connections'] if r!=old[r['connection_id']]];g=read_rr_graph('work/alu4_validation_capture_2026-10-05/rr_graph.xml');gate=check(g,bg,changed);r=json.loads((out/'receipt.json').read_text());before=r['metrics']['before'];after=r['metrics']['after'];accept=gate['accepted'] and after['scores']['predicted_channel_overuse_units']<=before['scores']['predicted_channel_overuse_units'] and after['pin_conflicts']['global_overuse_unique_net_units']<before['pin_conflicts']['global_overuse_unique_net_units']
record={'tree_gate':gate,'before':before,'after':after,'accepted_as_partial_repair':accept,'baseline_sha256':sha(bgpath),'candidate_sha256':sha(out/'prediction.json'),'decision_source_sha256':sha(__file__),'native_label_inputs':False,'scope':'single-class partial repair; not complete design capacity/native/timing legality'};(out/'decision.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='tree_gate'}),flush=True)
