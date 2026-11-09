"""Independent previous-state dirty scope, epochs and full-search chain equality."""
import json
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_sequential_feedback_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
P=E/'full_ram_sequential_feedback_v1_2026-10-09';C=E/'full_ram_swap_candidates_v1_2026-10-09';B=E/'full_ram_length_switch_prediction_v1_2026-10-09';graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml';epfile=E/'full_ram_comb_constant_endpoints_v1_2026-10-09/cw192.json'
r=json.loads((P/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_INCREMENTAL_DECISION'
for p,h in r['bindings'].items():assert sha(p)==h
g=read_rr_graph(graph);previous_ep=json.loads(epfile.read_text());previous_pred=json.loads((B/'prediction.json').read_text());epochs={c['connection_id']:1 for c in previous_ep['connections']};results=[];paths=[Path(__file__),P/'receipt.json',graph,epfile,B/'prediction.json']
for step in (1,2):
 ep_path=C/f'candidate_{step}/endpoints.json';pred_path=P/f'candidate_{step}/prediction.json';epoch_path=P/f'candidate_{step}/epochs.json';full_path=E/f'full_ram_swap_full_search_v1_2026-10-09/candidate_{step}/prediction.json';full_receipt=full_path.parent/'receipt.json'
 fr=json.loads(full_receipt.read_text());assert fr['status']=='COMPLETE_AUDITED_PREDICTION'
 for p,h in {**fr['bindings'],**fr['files']}.items():assert sha(p)==h
 ep=json.loads(ep_path.read_text());pred=json.loads(pred_path.read_text());full=json.loads(full_path.read_text());prev={c['connection_id']:c for c in previous_ep['connections']};oldpaths={c['connection_id']:c for c in previous_pred['connections']};fresh={c['connection_id']:c for c in full['connections']}
 assert len(prev)==len(fresh)==len(pred['connections'])==16819
 changed={c['connection_id'] for c in ep['connections'] if (c['source'],c['sink'])!=(prev[c['connection_id']]['source'],prev[c['connection_id']]['sink'])};selected={prev[c]['net_id'] for c in changed};updated={c['connection_id'] for c in ep['connections'] if c['net_id'] in selected}
 for c in pred['connections']:
  cid=c['connection_id'];assert all(c[k]==fresh[cid][k] for k in ('net_id','source','sink','physical_edge_ids'))
  if cid in updated:epochs[cid]=step+1
  else:assert c['physical_edge_ids']==oldpaths[cid]['physical_edge_ids']
 assert {int(k):v for k,v in json.loads(epoch_path.read_text()).items()}==epochs
 assert pred['node_occupancy']==full['node_occupancy'];checked=audit(g,ep,pred);reported=r['details']['reports'][step]
 assert len(changed)==reported['changed_endpoints'] and len(selected)==reported['affected_nets'] and len(updated)==reported['recomputed_connections']
 assert reported['committed_epoch']==step+1 and reported['invalid_and_stale_preserve_state']
 results.append(dict(step=step,changed_endpoints=len(changed),affected_nets=len(selected),updated_connections=len(updated),epoch_counts={str(e):sum(v==e for v in epochs.values()) for e in set(epochs.values())},all_core_paths_and_occupancy_equal_full_search=True,audit=checked));previous_ep=ep;previous_pred=pred;paths.extend([ep_path,pred_path,epoch_path,full_path,full_receipt])
out=dict(passed=True,results=results,bindings={str(p):sha(p) for p in paths},scope='Independent previous-endpoint selection, all epochs/retained paths and full-query equality. Rejection preservation is driver runtime assertion only; independent rejection replay still required. Not native route-tree legality or end-to-end benefit.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print([(x['step'],x['updated_connections'],x['epoch_counts']) for x in results])
