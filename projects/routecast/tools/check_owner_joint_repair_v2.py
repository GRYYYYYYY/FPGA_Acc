"""Explicit third-owner expansion fixture; no design identifiers in repair API."""
import sys,json,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from owner_joint_repair_v2 import repair,constrained_witness
from source_binding_v2 import closure
from pre_route_endpoints import sha
out=R/'experiments/owner_joint_repair_contract_v2_2026-10-07';out.mkdir();sources=closure([Path(__file__)]);(out/'protocol.json').write_text(json.dumps(dict(sources=sources,scope='Explicit third-owner expansion/complete reinsert fixture, not arbitrary graph or native proof.'))+'\n')
arcs=[(0,2,1),(0,3,1),(1,2,1),(2,4,1),(2,5,1),(3,4,1),(3,7,1),(6,3,1),(6,8,2),(8,7,1)];offset=[0];dest=[];inc=[];edge_by_pair={}
for u in range(9):
 for a,v,d in arcs:
  if a==u:edge_by_pair[u,v]=len(dest);dest.append(v);inc.append(d)
 offset.append(len(dest))
f=dict(row_offsets=offset,dest_ranks=dest,edge_ids=list(range(len(dest))),capacities=[1]*9)
class RC:
 scale=10**10;increments=inc
 def initial(self,n):return 0
 def path(self,src,sink,edges):
  u=src;d=0
  for e in edges:assert offset[u]<=e<offset[u+1];u=dest[e];d+=inc[e]
  assert u==sink;return d
rc=RC()
def record(cid,net,src,sink,path):return dict(connection_id=cid,net_id=net,source=src,sink=sink,answer=dict(status='FOUND',physical_edge_ids=[edge_by_pair[pair] for pair in path],delay=2),budget_integer=10,floor_integer=2)
before=[record(10,303,0,4,[(0,2),(2,4)]),record(20,202,6,7,[(6,3),(3,7)])];q=dict(connection_id=30,net_id=707,source=1,sink=5);floors={(0,4):2,(6,7):2,(1,5):2};snapshot=copy.deepcopy(before)
r=repair(f,rc,before,q,[303],floors,[0]*9,0,10,max_owner_nets=2);assert r['status']=='FOUND_JOINT_BATCH' and r['released_net_ids']==[202,303] and len(r['attempts'])==2;assert before==snapshot;assert {x['connection_id'] for x in r['solution']['records']}=={10,20,30};assert all(v<=f['capacities'][n] for n,v in r['solution']['ledger'].items())
for rec in r['solution']['records']:assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer']
assert any(e['blocking_net_ids']==[202] for e in r['attempts'][0]['expansion_evidence']);limited=repair(f,rc,before,q,[303],floors,[0]*9,0,10,max_owner_nets=1);assert limited['solution'] is None and before==snapshot
assert constrained_witness(f,rc,q,{q['source']}) is None
assert all(sha(k)==v for k,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),third_owner_discovered=True,full_cids_reinserted=True,caller_unchanged=True,owner_limit_failure_preserved=True,solution_global_required=10,local_completed=3),indent=2)+'\n');print('PASS witness expansion and joint repair')
