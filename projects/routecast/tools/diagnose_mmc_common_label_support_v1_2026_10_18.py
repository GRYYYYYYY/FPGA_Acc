"""Post-hoc initializer perturbation and native label-drift support diagnostic."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_common_native_label_matrix_v1_2026-10-18';proof=json.loads((D/'verification.json').read_text());assert proof['status']=='pass';P=json.loads((D/'protocol.json').read_text());frames={m:json.loads((R/p).read_text()) for m,p in P['predictions'].items()};records={m:{x['connection_id']:x for x in f['records']} for m,f in frames.items()};old=records['previous_native'];raw=records['raw'];local=records['local'];assert set(old)==set(raw)==set(local)
direct={cid for cid,x in raw.items() if (x['source'],x['sink'])!=(old[cid]['source'],old[cid]['sink'])};dirty_nets={raw[cid]['net_id'] for cid in direct};closure={cid for cid,x in raw.items() if x['net_id'] in dirty_nets};stable=closure-direct
for method in ['raw','local']:
 assert all(records[method][cid]['answer']['physical_edge_ids']==old[cid]['answer']['physical_edge_ids'] for cid in set(old)-closure)
changed={m:sum(records[m][cid]['answer']['physical_edge_ids']!=old[cid]['answer']['physical_edge_ids'] for cid in stable) for m in ['raw','local']}
v=json.loads((D/'vectors.json').read_text());channels=v['channels'];support={x['node'] for x in channels if any(x['predictions'][m]!=x['predictions']['previous_native'] for m in ['raw','local'])};drift=[]
for label in P['labels']:
 changed_truth={x['node'] for x in channels if x['labels'][label]!=x['predictions']['previous_native']}
 drift.append(dict(label=label,channel_occupancy_changed_from_old_native=len(changed_truth),outside_raw_local_update_support=len(changed_truth-support),outside_fraction=len(changed_truth-support)/len(changed_truth),scope='Descriptive native occupancy drift, not causal attribution to placement vs router/seed differences.'))
metrics=json.loads((D/'comparison.json').read_text())['metrics'];dominance=[]
for label in P['labels']:
 checks=[]
 for scope in ['concrete','spatial']:
  for name in ['spearman','precision_at_k','mae']:
   baseline=metrics[label]['previous_native'][scope][name];candidate=metrics[label]['local'][scope][name];eps=1e-12 if name!='precision_at_k' else 0
   at_least=baseline<=candidate+eps if name=='mae' else baseline>=candidate-eps
   strictly=baseline<candidate-eps if name=='mae' else baseline>candidate+eps
   checks.append(dict(scope=scope,metric=name,previous_native=baseline,local=candidate,at_least_as_good=at_least,strictly_better=strictly))
 dominance.append(dict(label=label,checks=checks,previous_footprint_dominates_local=all(x['at_least_as_good'] for x in checks) and any(x['strictly_better'] for x in checks)))
result=dict(bindings={str(D/'verification.json'):sha(D/'verification.json'),str(D/'comparison.json'):sha(D/'comparison.json'),str(D/'vectors.json'):sha(D/'vectors.json'),str(Path(__file__)):sha(__file__),**{str(R/p):sha(R/p) for p in P['predictions'].values()}},direct_endpoint_changed_connections=len(direct),dirty_complete_NETs=len(dirty_nets),dirty_closure_connections=len(closure),unchanged_endpoint_connections_in_dirty_NETs=len(stable),stable_endpoint_dirty_connections_whose_paths_changed=changed,untouched_NET_native_paths_unchanged_both_predictions=True,combined_channel_update_support=len(support),native_label_drift=drift,previous_native_control_comparisons=dominance,scope='Post-hoc mechanism diagnostic after frozen common-label experiment; no change to registered local-vs-raw gate. Retaining individually valid old paths may create parent conflicts when combined with new paths and requires a separately frozen repair/fallback policy and independent physical/budget/ledger checks. Not causal or unseen validation.')
with (D/'initializer_support_diagnostic_v1.json').open('x') as f:json.dump(result,f,indent=2)
print(json.dumps({k:x for k,x in result.items() if k not in ['bindings','previous_native_control_comparisons']}),flush=True)
