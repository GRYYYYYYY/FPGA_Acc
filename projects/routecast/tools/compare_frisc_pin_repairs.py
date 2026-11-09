"""Authenticated descriptive comparison; no prospective selector or speed claim."""
import argparse,json
from pathlib import Path
from pre_route_endpoints import sha
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('experiments/frisc_pin_repair_comparison_with_cost_2026-10-05'));p.add_argument('--full',type=Path);a=p.parse_args()
variants=[('BFS deterministic','frisc_pin_path_commit_2026-10-05'),('BFS minimum span','frisc_costed_pin_commit_2026-10-05'),('BFS frozen pressure','frisc_pressure_pin_commit_2026-10-05'),('weighted frozen pressure','frisc_weighted_pin_topology_commit_2026-10-05')]
if a.full:variants.append(('full conflict cohort weighted pressure',str(a.full)))
reports=[];inputs={};baseline=None
for name,directory in variants:
 root=Path(directory) if Path(directory).is_dir() else Path('experiments')/directory
 file=root/'receipt.json';r=json.loads(file.read_text());inputs[str(file)]=sha(file)
 assert sha(root/'prediction.json')==r['prediction_sha256']
 for path,digest in r['input_sha256'].items():assert sha(path)==digest
 for path,digest in r['source_sha256'].items():assert sha(root/'source'/path)==digest
 if baseline is None:baseline=r['metrics']['before']
 assert baseline==r['metrics']['before']
 before=baseline['scores'];after=r['metrics']['after'];scores=after['scores'];topology=r.get('net_union_topology',{}).get('after')
 reports.append({'variant':name,'updated_requests':r['updated_requests'],'retained_requests':r['retained_requests'],'channel_net_span':scores['channel_net_span_sum'],'span_delta':scores['channel_net_span_sum']-before['channel_net_span_sum'],'channel_overuse':scores['predicted_channel_overuse_units'],'overuse_delta':scores['predicted_channel_overuse_units']-before['predicted_channel_overuse_units'],'global_pin_overuse':after['pin_conflicts']['global_overuse_unique_net_units'],'target_class_pin_overuse':after['pin_conflicts']['target_class_overuse_units'],'commit_driver_full_wall_s':r['full_wall_s'],'commit_s':r['commit_s'],'topology':{k:topology[k] for k in ('net_count','internal_reconvergent_net_count','cyclic_net_count','terminal_alias_net_count')} if topology else 'not archived in this driver run'})
preparation=[]
for name,directory in [('BFS candidate generation','frisc_reachable_pin_trial_2026-10-05'),('BFS span assignment','frisc_costed_pin_assignment_2026-10-05'),('BFS pressure assignment','frisc_pressure_pin_assignment_2026-10-05'),('weighted candidate generation and assignment','frisc_weighted_pin_trial_2026-10-05')]:
 file=Path('experiments')/directory/'receipt.json';r=json.loads(file.read_text());inputs[str(file)]=sha(file);preparation.append({'stage':name,'full_wall_s':r['full_wall_s'],'query_wall_s':r.get('query_wall_s'),'solver_s':r.get('solver_wall_s',r.get('solver_s'))})
a.output.mkdir();receipt={'baseline':baseline,'variants':reports,'preparation_stages':preparation,'input_receipt_sha256':inputs,'comparator_sha256':sha(__file__),'limitations':['descriptive development comparisons, no prospective policy selection','commit driver wall time excludes candidate generation and matching; no speedup inference','single 26-request cohort unless explicit full variant supplied','pin/channel overuse and structural diagnostics are not native routing or timing legality']};(a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
lines=['| Variant | Requests | Span delta | Channel overuse delta | Global pin overuse |','|---|---:|---:|---:|---:|']
for r in reports:lines.append(f"| {r['variant']} | {r['updated_requests']} | {r['span_delta']:+d} | {r['overuse_delta']:+d} | {r['global_pin_overuse']} |")
(a.output/'comparison.md').write_text('\n'.join(lines)+'\n\nCommit times exclude candidate generation and matching. These are development diagnostics, not native QoR results.\n');print('\n'.join(lines))
