"""Small conflict fixture, input isolation, limits and arbitrary NET identities."""
import sys,json,copy,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from joint_owner_occupancy_memo_v4 import joint_route
from joint_owner_constraints_memo_v3 import joint_route as reference
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/joint_owner_occupancy_contract_v4b_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(sources=sources,scope='Explicit software conflict/API fixture, not native or arbitrary problem completeness.'))+'\n')
f=dict(row_offsets=[0,2,3,5,6,6,6],dest_ranks=[2,3,2,4,5,4],edge_ids=list(range(6)),capacities=[1]*6)
class RC:
 scale=10**10;increments=[1,2,1,1,1,1]
 def initial(self,n):return 0
 def path(self,src,sink,edges):
  total=0;u=src
  for e in edges:
   assert f['row_offsets'][u]<=e<f['row_offsets'][u+1];total+=self.increments[e];u=f['dest_ranks'][e]
  assert u==sink;return total
rc=RC();groups={303:[dict(connection_id=100,net_id=303,source=0,sink=4)],707:[dict(connection_id=200,net_id=707,source=1,sink=5)]};floors={(0,4):2,(1,5):2};before=copy.deepcopy((f,groups,floors))
def call(**kwargs):return joint_route(f,rc,groups,floors,[],[0]*6,0,7,**kwargs)
def hostile_observer(entry,states,solution):
 entry['status']='changed'
 for state in states.values():state['records'].clear()
 if solution is not None:solution['records'].clear()
r=call(observer=hostile_observer,reuse_groups=True);assert r['status']=='FOUND_JOINT_BATCH' and len(r['branches'])==2 and len(r['solution']['records'])==2 and r['solution']['required_connections']==7;assert (f,groups,floors)==before
for rec in r['solution']['records']:assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']
assert r['branches'][0]['conflict_node']==2 and r['branches'][1]['constraints']==[(303,2)];assert r['solution']['ledger'][2]==1
plain=call();cached=call(reuse_groups=True);assert plain['solution']==cached['solution'] and plain['branches']==cached['branches'];assert cached['low_level_reuses']==1 and cached['low_level_computations']==3
assert call(frontier='dfs')['status']=='FOUND_JOINT_BATCH'
for frontier in ('bfs','dfs'):
 for reuse in (False,True):
  assert call(frontier=frontier,reuse_groups=reuse)==reference(f,rc,groups,floors,[],[0]*6,0,7,frontier=frontier,reuse_groups=reuse)
assert call(max_joint_nodes=1)['status']=='JOINT_NODE_LIMIT';assert call(deadline=time.perf_counter()-1)['status']=='DEADLINE'
f['capacities'][2]=2;r=call();assert len(r['branches'])==1 and r['solution']['ledger'][2]==2;f['capacities'][2]=1
for invalid in (0,-1,True):
 try:call(max_joint_nodes=invalid)
 except ValueError:pass
 else:raise AssertionError('invalid joint bound accepted')
bad=copy.deepcopy(groups);bad[707][0]['connection_id']=100
try:joint_route(f,rc,bad,floors,[],[0]*6,0,7)
except ValueError:pass
else:raise AssertionError('duplicate CID accepted')
assert all(sha(k)==v for k,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),joint_conflict_resolved=True,arbitrary_net_ids=True,global_required_preserved=True,caller_and_observer_isolation_pass=True,node_deadline_limits_pass=True,capacity_two_pass=True,invalid_parameters_rejected=True),indent=2)+'\n');print('PASS reusable joint API')
