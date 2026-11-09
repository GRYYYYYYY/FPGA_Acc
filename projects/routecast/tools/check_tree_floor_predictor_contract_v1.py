"""Meaningful budget/capacity/shared-owner contracts on explicit small CSR."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from tree_floor_predictor_v1 import predict,grouped_floor
class RC:
 scale=10**9
 increments=[6,6,6]
 def initial(self,n):return 0
 def path(self,source,sink,edges):
  u=source;delay=0;seen={u}
  for eid in edges:
   a,v=arcs[eid];assert a==u and v not in seen;u=v;seen.add(v);delay+=self.increments[eid]
  assert u==sink;return delay
arcs=[(0,1),(1,2),(1,3)];f=dict(row_offsets=[0,1,3,3,3],dest_ranks=[1,2,3],edge_ids=[0,1,2],capacities=[1,1,1,1]);rc=RC();queries=[dict(connection_id=0,net_id=0,source=0,sink=2),dict(connection_id=1,net_id=0,source=0,sink=3)];floors={(0,v):d for v,d in grouped_floor(f,rc,0,[2,3]).items()};assert floors=={(0,2):12,(0,3):12}
r=predict(f,rc,queries,floors);assert r['completed_connections']==2 and r['ledger']=={0:1,1:1,2:1,3:1};assert [x['answer']['physical_edge_ids'] for x in r['records']]==[[0,1],[0,2]]
# A different NET cannot consume an already full shared trunk or source.
blocked=predict(f,rc,[*queries,dict(connection_id=2,net_id=1,source=0,sink=2)],floors);assert blocked['completed_connections']==2 and blocked['failure']['status']=='SOURCE_CAPACITY' and blocked['ledger']==r['ledger'] and blocked['records']==r['records']
rc.increments=[600000000]*3;floors={(0,v):d for v,d in grouped_floor(f,rc,0,[2,3]).items()};assert all(d==1200000000 for d in floors.values())
legacy=predict(f,rc,queries,floors,floor_budget=False);scaled=predict(f,rc,queries,floors,floor_budget=True);assert legacy['completed_connections']==0 and not legacy['ledger'] and scaled['completed_connections']==2 and scaled['records'][0]['budget_integer']==1800000000
root=predict(f,rc,queries,floors,tree=False);assert root['records']==scaled['records'] and root['ledger']==scaled['ledger']
out=R/'experiments/tree_floor_predictor_contract_v1_2026-10-07';out.mkdir();(out/'receipt.json').write_text(json.dumps(dict(shared_net_trunk_counted_once=True,capacity_failure_keeps_prior_records_and_ledger=True,hard_budget_rejection_and_floor_budget_acceptance=True,root_tree_simple_fixture_parity=True,inputs={str(Path(__file__)):sha(__file__),str(R/'tools/tree_floor_predictor_v1.py'):sha(R/'tools/tree_floor_predictor_v1.py')},scope='Explicit small CSR semantic cases; does not prove arbitrary loaded RC timing or complete native routing.'),indent=2)+'\n');print('PASS')
