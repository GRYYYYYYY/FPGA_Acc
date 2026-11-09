"""Exercise the actual frozen driver transaction loop on a budget-retention toy graph."""
import sys,ast,json,copy,heapq,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
source=R/'tools/trial_soft_demand_feedback_v1.py';tree=ast.parse(source.read_text());defs=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('own','rebuild')];outer=next(x for x in tree.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='round_index');transaction=next(x for x in outer.body if isinstance(x,ast.For) and isinstance(x.target,ast.Name) and x.target.id=='net');code=compile(ast.fix_missing_locations(ast.Module(body=defs+[transaction],type_ignores=[])),str(source),'exec')
f=dict(row_offsets=[0,2,2,3,4],dest_ranks=[1,2,1,2],edge_ids=[0,1,2,3],capacities=[1]*4);slots={i:i for i in range(4)}
class RC:
 increments=[100,40,45,5]
 def initial(self,n):return 0
 def path(self,source,sink,edges):
  u=source;total=0
  for e in edges:assert f['row_offsets'][u]<=e<f['row_offsets'][u+1];u=f['dest_ranks'][e];total+=self.increments[e]
  assert u==sink;return total
cases=[]
for label,budget,price,expected_status,expected_nodes in [('budget_failure_retains_all',90,100,'RETAIN_BUDGET_OR_UNREACHABLE',{0:1,1:1,2:2,3:1}),('valid_same_tree_epoch',90,0,'COMMITTED',{0:1,1:1,2:2,3:1}),('replace_keeps_other_NET_charge',110,100,'COMMITTED',{0:1,1:1,2:1,3:1})]:
 q=dict(connection_id=0,net_id=7,source=0,sink=1);other=dict(connection_id=1,net_id=8,source=3,sink=2);old=dict(q,answer=dict(status='FOUND',physical_edge_ids=[1,2],delay=85),budget_integer=budget,floor_integer=60);keep=dict(other,answer=dict(status='FOUND',physical_edge_ids=[3],delay=5),budget_integer=90,floor_integer=3);records={7:[old],8:[keep]};before=copy.deepcopy(records);ledger=Counter({0:1,1:1,2:2,3:1});scope=dict(f=f,slots=slots,rc=RC(),nodes=list(range(4)),groups={7:[q],8:[other]},records=records,queries=[q,other],owned={7:{0,1,2},8:{3,2}},ledger=ledger,prices=Counter({2:price}),weight=1,epochs={7:1,8:1},affected=[7],events=[],heapq=heapq,Counter=Counter);exec(code,scope);event=scope['events'][0];assert event['status']==expected_status and dict(scope['ledger'])==expected_nodes and scope['records'][8]==before[8] and scope['epochs'][8]==1
 if expected_status.startswith('RETAIN'):assert scope['records']==before and scope['epochs']=={7:1,8:1} and event['failed_connection_ids']==[0]
 else:assert scope['epochs'][7]==2
 cases.append(dict(case=label,status=event['status'],ledger=dict(scope['ledger']),epochs=scope['epochs']));print('PASS actual-loop fixture',label,flush=True)
out=R/'experiments/soft_feedback_retention_contract_v1_2026-10-07';out.mkdir();bindings={**closure([Path(__file__)]),str(source):sha(source)};(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,cases=cases,scope='Actual frozen driver transaction loop executed on explicit toy integer RC graph. Budget failure chooses weighted direct path100>budget90 and preserves whole old path85/state; replacement keeps anotherNET charge. Not actual VPR/native/shortest completeness/heldout evidence.'),indent=2)+'\n')
