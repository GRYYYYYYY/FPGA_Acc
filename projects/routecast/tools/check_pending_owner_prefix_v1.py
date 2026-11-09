"""Whole-NET, request-scope and ordered window selector fixture."""
import sys,json,copy,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pending_owner_prefix_v1 import select
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/pending_owner_prefix_contract_v1_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(sources=sources,scope='Selector scope/owner fixture, no combined path or native proof.'))+'\n')
f=dict(row_offsets=[0,1,2,3,3,4,4],dest_ranks=[2,4,3,5],edge_ids=list(range(4)),capacities=[1]*6)
class RC:
 increments=[1]*4
 def initial(self,n):return 0
 def path(self,src,sink,edges):
  u=src
  for e in edges:assert f['row_offsets'][u]<=e<f['row_offsets'][u+1];u=f['dest_ranks'][e]
  assert u==sink;return len(edges)
before=[dict(connection_id=i,net_id=42,source=0,sink=3,answer=dict(physical_edge_ids=[0,2])) for i in (5,6)]+[dict(connection_id=7,net_id=77,source=1,sink=5,answer=dict(physical_edge_ids=[1,3]))];pending=[dict(connection_id=11,net_id=101,source=1,sink=5),dict(connection_id=10,net_id=100,source=0,sink=3)];snapshot=copy.deepcopy((before,pending));r=select(f,RC(),before,pending,max_owner_nets=1);assert r['requested_connection_ids']==[10] and r['released_net_ids']==[42] and r['removed_connection_ids']==[5,6] and r['remaining_pending_ids']==[11] and r['stop']=='OWNER_LIMIT';assert (before,pending)==snapshot
r=select(f,RC(),before,pending,max_queries=1);assert r['stop']=='WINDOW_LIMIT' and r['requested_connection_ids']==[10];r=select(f,RC(),before,pending,max_owner_nets=2);assert r['stop']=='ALL_PENDING_SELECTED' and r['requested_connection_ids']==[10,11] and set(r['removed_connection_ids'])=={5,6,7};assert select(f,RC(),before,pending,deadline=time.perf_counter()-1)['stop']=='DEADLINE'
try:select(f,RC(),before,[pending[0],pending[0]])
except ValueError:pass
else:raise AssertionError('duplicate pending accepted')
assert all(sha(k)==v for k,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),whole_net_removed=True,ordered_requested_remaining_scope_pass=True,owner_window_deadline_limits_pass=True,caller_unchanged=True,duplicate_ids_rejected=True),indent=2)+'\n');print('PASS pending owner prefix')
