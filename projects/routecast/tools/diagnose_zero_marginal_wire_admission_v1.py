"""Complete census of a provable no-improvement guard, without new search runs."""
import json,sys
from pathlib import Path
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
P=R/'experiments/complete_wire_search_cost_replay_v2_2026-10-08';proof=json.loads((P/'verification.json').read_text());assert proof['all_complete_cohort_fidelity_and_cost_arithmetic_checks_pass'] and all(sha(f)==h for f,h in proof['bindings'].items());bindings={**proof['bindings'],str(P/'verification.json'):sha(P/'verification.json'),**closure([Path(__file__)])};profile=json.loads((P/'receipt.json').read_text())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
graph,digest,nodes,f,rc,queries=load_endpoints(Path(case['target']));length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
base=json.loads((R/'experiments/critical_owner_transaction_v1_2026-10-08/receipt.json').read_text())['rows'][0]['state'];ledger=SharedTreeLedger({int(cid):path for cid,path in base.items()},{q['connection_id']:q for q in queries},f['capacities'],length)
D=R/'experiments/zero_marginal_wire_admission_v1_2026-10-08';D.mkdir(exist_ok=False);reports=[]
for run in profile['complete_passes']:
 receipt=json.loads((R/'experiments'/run['name']/'receipt.json').read_text());rows=[]
 for event,clock in zip(receipt['events'],run['rows']):
  cid=event['connection_id'];net=ledger.queries[cid]['net_id'];kept,fixed=ledger.view(cid);margin=ledger.wire[net]-sum(length.get(n,0) for n in kept);assert margin>=0
  eligible=clock['searched'] and margin==0
  if eligible:assert event['status']!='COMMIT'
  rows.append(dict(connection_id=cid,old_marginal_wire=margin,certified_no_strict_wire_improvement=eligible,baseline_search_seconds=clock.get('search_seconds',0),baseline_labels_created=clock.get('labels_created',0),baseline_examined_edges=clock.get('examined_edges',0)))
  if event['status']=='COMMIT':ledger.replace(cid,event['new_path'])
 assert ledger.state=={int(cid):tuple(tuple(x) for x in path) for cid,path in receipt['state'].items()} and len(rows)==1929
 guarded=[x for x in rows if x['certified_no_strict_wire_improvement']]
 reports.append(dict(name=run['name'],complete_queries=1929,guarded_search_calls=len(guarded),historical_guarded_search_seconds=sum(x['baseline_search_seconds'] for x in guarded),historical_guarded_labels=sum(x['baseline_labels_created'] for x in guarded),historical_guarded_examined_edges=sum(x['baseline_examined_edges'] for x in guarded),rows=rows))
assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,complete_events=5787,passes=reports,guarded_search_calls=sum(x['guarded_search_calls'] for x in reports),historical_guarded_search_seconds=sum(x['historical_guarded_search_seconds'] for x in reports),scope='Complete census only, not execution timing of a new routing algorithm. For fixed kept branches, new NET union wire >= kept wire by nonnegative channel spans. If old union equals kept wire, no strict wire decrease is possible; retain all existing demands/paths and original budget failures. Historical component costs are attribution, not actual savings or end-to-end gain.')
(D/'diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ('bindings','passes')},flush=True)
for x in reports:print({k:v for k,v in x.items() if k!='rows'},flush=True)
