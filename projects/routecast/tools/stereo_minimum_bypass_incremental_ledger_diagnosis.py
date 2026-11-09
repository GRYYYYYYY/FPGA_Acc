"""Whole-net closure composition of five over-budget diagnostic bypasses."""
import json,time,shutil
from pathlib import Path
from collections import defaultdict,Counter
from types import SimpleNamespace
from prepared_csr import read
from pre_route_endpoints import sha
from streaming_prediction_audit import Nodes,Edges
from physical_prediction_audit import audit
from net_union_topology import diagnose
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'minimum_bypass_incremental_ledger_diagnosis';out.mkdir();(out/'source').mkdir();start=time.monotonic()
 paths=[b/'completed_high_fanout_snapshots'/f'net_{n}.json' for n in (3861,17288)]+[b/'conflict_minimum_bypass_delay/results.json',b/'conflict_minimum_bypass_delay/receipt.json',b/'minimum_bypass_physical_audit_v2/receipt.json',b/'additional_high_fanout_physical_audit/receipt.json',b/'additional_high_fanout_physical_audit/conflict_repair_requests.json',b/'streaming_csr_class_cache_v3/csr/manifest.json']
 inputs={str(p):sha(p) for p in paths};sources={n:sha(Path('tools')/n) for n in ['stereo_minimum_bypass_incremental_ledger_diagnosis.py','prepared_csr.py','pre_route_endpoints.py','streaming_prediction_audit.py','physical_prediction_audit.py','net_union_topology.py','rr_graph.py','rr_local_batch_occupancy.py','rr_occupancy.py','connection_golden.py']}
 for n in sources:shutil.copyfile(Path('tools')/n,out/'source'/n)
 for folder in ('minimum_bypass_physical_audit_v2','additional_high_fanout_physical_audit'):
  r=b/folder;receipt=json.loads((r/'receipt.json').read_text());protocol=json.loads((r/'protocol.json').read_text());assert receipt['protocol_sha256']==sha(r/'protocol.json') and receipt['physical_audit']['all_physical_and_union_checks_passed']
  assert all(sha(k)==h for k,h in protocol['snapshots'].items())
 bypass=json.loads(paths[2].read_text());assert json.loads(paths[3].read_text())['results_sha256']==sha(paths[2]);assert len(bypass)==5 and all(x['status']=='FOUND' and not x['fits_original_budget'] for x in bypass)
 snapshots=[json.loads(p.read_text()) for p in paths[:2]];graph=json.loads((b/'conflict_minimum_bypass_delay/protocol.json').read_text())['graph_sha256'];_,f=read(b/'streaming_csr_class_cache_v3/csr',graph)
 rows=[{**x,'physical_edge_ids':s['net_result']['result']['paths'][str(x['sink'])],'method':'original'} for s in snapshots for x in s['connections']];assert len(rows)==429
 changes={x['connection_id']:x['physical_edge_ids'] for x in bypass};assert len(changes)==5 and set(changes)<=set(x['connection_id'] for x in rows)
 modified=[{**x,'physical_edge_ids':changes.get(x['connection_id'],x['physical_edge_ids']),'method':'diagnostic_bypass' if x['connection_id'] in changes else 'original'} for x in rows];records={};users=[]
 for cohort in (rows,modified):
  occupied=defaultdict(set)
  for row in cohort:
   n=row['source'];occupied[n].add(row['net_id'])
   for eid in row['physical_edge_ids']:
    matches=[i for i in range(f['row_offsets'][n],f['row_offsets'][n+1]) if f['edge_ids'][i]==eid];assert len(matches)==1;i=matches[0];d=f['dest_ranks'][i];records[eid]=SimpleNamespace(source=n,sink=d,switch_id=f['switch_ids'][i]);n=d;occupied[n].add(row['net_id'])
   assert n==row['sink']
  users.append(occupied)
 g=SimpleNamespace(nodes=Nodes(f['types'],f['capacities']),edges=Edges(records,len(f['edge_ids'])),sha256=graph);ep={'graph_sha256':graph,'connections':[{k:x[k] for k in ('connection_id','net_id','source','sink')} for x in rows]};reports=[]
 for name,cohort,occupied in zip(('original','diagnostic_replacement'),(rows,modified),users):
  pred={'physical_graph_sha256':graph,'connections':cohort,'requested':429,'completed':429,'node_occupancy':{str(n):len(v) for n,v in occupied.items()},'methods':dict(Counter(x['method'] for x in cohort))}
  checked=audit(g,ep,pred);topology=diagnose(g,pred);conflicts=[{'rr_node':n,'unique_nets':sorted(v),'capacity':f['capacities'][n]} for n,v in occupied.items() if len(v)>f['capacities'][n]]
  reports.append({'name':name,'physical_checks':checked,'topology':topology,'overflow_units':sum(len(x['unique_nets'])-x['capacity'] for x in conflicts),'conflicts':conflicts})
 sparse=SimpleNamespace(nodes={n:g.nodes[n] for n in set(users[0])|set(users[1])},edges=g.edges,sha256=graph)
 ledger=LocalBatchOccupancy(sparse)
 def update(row,epoch):return {k:row[k] for k in ('connection_id','net_id','source','sink')}|{'epoch':epoch,'edge_ids':row['physical_edge_ids']}
 assert ledger.update_batch([update(row,1) for row in rows])==Result.COMMITTED
 assert {n:v for n,v in ledger.occupancy.items() if v}=={n:len(v) for n,v in users[0].items()}
 before=ledger.states;ts=time.monotonic();assert ledger.update_batch([update(row,2) for row in modified if row['connection_id'] in changes])==Result.COMMITTED;incremental_s=time.monotonic()-ts
 assert {n:v for n,v in ledger.occupancy.items() if v}=={n:len(v) for n,v in users[1].items()}
 assert ledger.occupancy==ledger.rebuild() and not ledger.overflow()
 assert all(ledger.states[row['connection_id']]==before[row['connection_id']] for row in rows if row['connection_id'] not in changes)
 after=ledger.states;assert ledger.update_batch([update(row,2) for row in modified if row['connection_id'] in changes])==Result.STALE;assert ledger.states==after
 assert all(sha(k)==h for k,h in inputs.items()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
 protocol={'inputs':inputs,'sources':sources,'graph_sha256':graph,'scope':'429-connection two-net closure diagnosis on authenticated CSR and originalXML-audited paths; bypasses exceed original budgets; no global ownership, native legality or commit'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 report={'incremental_update_s':incremental_s,'incremental_matches_complete_rebuild':True,'unchanged_states_exact':True,'stale_replay_no_mutation':True,'ledger_scope':'isolated occupancy implementation simulation; Result.COMMITTED is occupancy publication only, not budget or route legality acceptance','connections':429,'replaced':5,'unchanged':424,'reports':reports,'budget_gate_passed':False,'committed':False,'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':run()
