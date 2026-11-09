"""Explicit rollback, limits, deadline, and duplicate identity contracts."""
import json,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from mcnc_bounded_owner_sequence_v1 import sequence
from tree_floor_predictor_seed_v3 import predict
class RC:
 scale=10**9;increments=[1,1]
 def initial(self,n):return 0
 def path(self,source,sink,edges):
  assert source==0 and sink==2 and edges==[0,1];return 2
f=dict(row_offsets=[0,1,2,2],dest_ranks=[1,2],edge_ids=[0,1],capacities=[1,1,1]);queries=[dict(connection_id=0,net_id=0,source=0,sink=2),dict(connection_id=1,net_id=1,source=0,sink=2)];floors={(0,2):2};state,events,stop=sequence(f,RC(),queries,floors);assert stop=='SOURCE_CAPACITY' and not events and state['completed_connections']==1
# Distinct SOURCE nodes share a single capacity-1 channel: owner batch fails
# on reinsert, so the complete before snapshot must survive.
class RC2:
 scale=10**9;increments=[1,1,1,1]
 def initial(self,n):return 0
 def path(self,source,sink,edges):
  arc=[(0,2),(1,2),(2,3),(2,4)];u=source
  for eid in edges:a,v=arc[eid];assert a==u;u=v
  assert u==sink;return len(edges)
f2=dict(row_offsets=[0,1,2,4,4,4],dest_ranks=[2,2,3,4],edge_ids=[0,1,2,3],capacities=[1]*5);qs=[dict(connection_id=0,net_id=0,source=0,sink=3),dict(connection_id=1,net_id=1,source=1,sink=4)];fl={(0,3):2,(1,4):2};before=predict(f2,RC2(),qs,fl);state,events,stop=sequence(f2,RC2(),qs,fl);assert stop=='BATCH_ROLLBACK' and len(events)==1 and not events[0]['committed'];assert state['records']==before['records'] and state['ledger']==before['ledger'];assert events[0]['working_records'][0]['connection_id']==1
state,events,stop=sequence(f2,RC2(),qs,fl,max_batches=0);assert stop=='BATCH_LIMIT' and not events
state,events,stop=sequence(f2,RC2(),qs,fl,max_owner_nets=0);assert stop=='OWNER_LIMIT' and not events
state,events,stop=sequence(f2,RC2(),qs,fl,deadline=time.perf_counter()-1);assert stop=='DEADLINE' and not state['records']
try:predict(f2,RC2(),[qs[0],qs[0]],fl)
except ValueError:pass
else:raise AssertionError('duplicate new CID accepted')
out=R/'experiments/bounded_owner_sequence_contract_v1_2026-10-07';out.mkdir();(out/'receipt.json').write_text(json.dumps(dict(rollback_preserves_all_before_records_ledger=True,batch_limit_pass=True,owner_limit_pass=True,deadline_pass=True,duplicate_new_query_rejected=True,source_capacity_terminal_pass=True,bindings={str(Path(__file__)):sha(__file__),str(R/'tools/mcnc_bounded_owner_sequence_v1.py'):sha(R/'tools/mcnc_bounded_owner_sequence_v1.py'),str(R/'tools/tree_floor_predictor_seed_v3.py'):sha(R/'tools/tree_floor_predictor_seed_v3.py')},scope='Synthetic software ownership and bounded termination; not native persistent epoch or arbitrary exception rollback.'),indent=2)+'\n');print('PASS')
