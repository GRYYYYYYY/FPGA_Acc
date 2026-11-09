"""Seed ownership failure/alias/duplicate query checks with exact small graph."""
import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from tree_floor_predictor_seed_v2 import predict
class RC:
 scale=10**9;increments=[1,1]
 def initial(self,n):return 0
 def path(self,source,sink,edges):
  assert source==0 and sink==2 and edges==[0,1];return 2
f=dict(row_offsets=[0,1,2,2],dest_ranks=[1,2],edge_ids=[0,1],capacities=[1,1,1]);seed=[dict(connection_id=0,net_id=7,source=0,sink=2,answer=dict(status='FOUND',physical_edge_ids=[0,1],delay=2),budget_integer=10**9,floor_integer=2)];before=json.dumps(seed,sort_keys=True);q=dict(connection_id=1,net_id=8,source=0,sink=2);floors={(0,2):2};out=R/'experiments/seed_tree_failure_contract_v1_2026-10-07';out.mkdir();bindings={str(Path(__file__)):sha(__file__),str(R/'tools/tree_floor_predictor_seed_v2.py'):sha(R/'tools/tree_floor_predictor_seed_v2.py')};(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings))+'\n')
r=predict(f,RC(),[q],floors,seed_records=seed);assert r['failure']['status']=='SOURCE_CAPACITY' and r['records']==seed and r['ledger']=={0:1,1:1,2:1};accepted=seed if r['failure'] else r['records'];assert accepted==seed
r['records'][0]['answer']['physical_edge_ids'][0]=99;assert json.dumps(seed,sort_keys=True)==before
try:predict(f,RC(),[dict(q,connection_id=0)],floors,seed_records=seed)
except ValueError:pass
else:raise AssertionError('duplicate retained query allowed')
assert json.dumps(seed,sort_keys=True)==before and all(sha(p)==h for p,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(source_capacity_failure_keeps_retained_records_ledger=True,caller_seed_path_storage_not_aliased=True,duplicate_query_rejected=True,bindings=bindings,scope='Small software ownership semantics; not durable native rollback or all arbitrary exceptions.'),indent=2)+'\n');print('PASS')
