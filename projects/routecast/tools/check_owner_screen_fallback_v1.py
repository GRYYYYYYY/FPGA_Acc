"""Shortest witness exceeds owner cap but longer single-owner alternative succeeds."""
import sys,json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from owner_joint_repair_v2 import repair
from source_binding_v2 import closure
from pre_route_endpoints import sha
out=R/'experiments/owner_screen_fallback_contract_v1_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(sources=sources,scope='Explicit longer-path/fewer-owner bounded fallback fixture.'))+'\n')
arcs=[(0,2,1),(0,3,1),(0,6,2),(1,2,1),(2,4,1),(2,5,1),(3,9,1),(6,4,2),(6,13,1),(7,3,1),(3,10,1),(8,9,1),(9,4,1),(9,11,1),(12,6,1),(12,14,2),(14,13,1)];offset=[0];dst=[];inc=[];by={}
for u in range(15):
 for a,v,w in arcs:
  if a==u:by[u,v]=len(dst);dst.append(v);inc.append(w)
 offset.append(len(dst))
f=dict(row_offsets=offset,dest_ranks=dst,edge_ids=list(range(len(dst))),capacities=[1]*15)
class RC:
 scale=10**10;increments=inc
 def initial(self,n):return 0
 def path(self,src,sink,edges):
  d=0;u=src
  for e in edges:assert offset[u]<=e<offset[u+1];u=dst[e];d+=inc[e]
  assert u==sink;return d
rc=RC()
def record(cid,net,src,sink,pairs):return dict(connection_id=cid,net_id=net,source=src,sink=sink,answer=dict(status='FOUND',physical_edge_ids=[by[p] for p in pairs],delay=2),budget_integer=10,floor_integer=2)
before=[record(10,303,0,4,[(0,2),(2,4)]),record(20,202,7,10,[(7,3),(3,10)]),record(30,404,8,11,[(8,9),(9,11)]),record(40,606,12,13,[(12,6),(6,13)])];snapshot=copy.deepcopy(before);q=dict(connection_id=50,net_id=707,source=1,sink=5);floors={(r['source'],r['sink']):2 for r in before};floors[1,5]=2
result=repair(f,rc,before,q,[303],floors,[0]*15,0,9,max_owner_nets=2);assert result['solution'] is not None and result['released_net_ids']==[303,606];fallback=result['attempts'][0]['fallback_evidence'][0];assert fallback['baseline'] is None and fallback['status']=='BASELINE_FAILED_FILTER_VALID';assert result['owner_checks']<=32 and result['screens']<=4;assert before==snapshot;assert len(result['solution']['records'])==5
for rec in result['solution']['records']:assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer']
assert all(sha(k)==v for k,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),oversized_shortest_witness_fallback_pass=True,baseline_precondition_checked=True,whole_owner_reinserted=True,caller_unchanged=True,bounded_checks=True),indent=2)+'\n');print('PASS bounded screened fallback')
