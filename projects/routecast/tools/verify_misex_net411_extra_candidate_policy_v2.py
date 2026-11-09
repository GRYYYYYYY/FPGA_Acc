"""Independent bounded proposal scope, ordering and rollback receipt checks."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/misex_net411_extra_owner_joint_v2_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());source=R/'experiments/misex_net411_failure_owner_domains_v1_2026-10-07/receipt.json';e=out/'event.json';pr=json.loads(source.read_text());event=json.loads(e.read_text());counts=Counter(rec['net_id'] for rec in event['before_records']);coverage=defaultdict(set)
for row in pr['rows']:
 for check in row['checks']:
  if check['witness'] is not None:coverage[tuple(sorted(set(row['release'])|{check['extra_net']}))].add(row['query']['connection_id'])
positive=[(frozenset(row['release']),check['extra_net'],row['query']['connection_id']) for row in pr['rows'] for check in row['checks'] if check['witness'] is not None]
for i,(base,owner,cid) in enumerate(positive):
 for base2,owner2,cid2 in positive[i+1:]:
  if base!=base2 or owner==owner2:continue
  union=tuple(sorted(base|{owner,owner2}))
  if len(union)<=7:coverage[union].update({cid,cid2})
coverage={ns:cids for ns,cids in coverage.items() if len(ns)<=7};ordered=sorted(coverage,key=lambda ns:(-len(coverage[ns]),sum(counts[net] for net in ns),ns))[:8];candidates=json.loads((out/'candidates.json').read_text());assert candidates==[dict(release=list(ns),restored_failed_connection_ids=sorted(coverage[ns])) for ns in ordered]
for index,attempt in enumerate(r['attempts']):
 assert attempt['index']==index and attempt['release']==list(ordered[index]) and 1<=len(attempt['release'])<=7;assert attempt['removed_connection_ids']==[rec['connection_id'] for rec in event['before_records'] if rec['net_id'] in attempt['release']]
solution=json.loads((out/'candidate.json').read_text());allowed={rec['connection_id'] for rec in event['before_records']}|set(event['selection']['requested_connection_ids'])
if solution is None:assert r['completed'] is None
else:
 records={rec['connection_id']:rec for rec in solution['records']};assert len(records)==len(solution['records']) and set(records)==allowed and solution['required_connections']==r['required']==2449;assert r['completed']==len(allowed);release=set(r['attempts'][-1]['release']);assert all(records[rec['connection_id']]==rec for rec in event['before_records'] if rec['net_id'] not in release)
assert all(sha(k)==h for k,h in bindings.items());(out/'candidate_policy_verification.json').write_text(json.dumps(dict(candidate_order_and_scope_verified=True,all_selected_and_whole_net_scope_verified=True,local_solution_present=solution is not None,bindings=bindings),indent=2)+'\n');print('PASS candidate policy',len(r['attempts']),solution is not None)
