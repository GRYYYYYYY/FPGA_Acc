"""Independently rebuild all real path-choice/capacity/parent clauses and variable roles."""
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
from unified_rr_audit_inventory_v2 import read
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_full909_cnf_v1_2026-10-09';D=E/'adder_full909_cnf_structure_verification_v1_2026-10-09';D.mkdir(exist_ok=False);rp=B/'verification.json';r=json.loads(rp.read_text());assert all(sha(p)==h for p,h in r['bindings'].items());bindings={**r['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};ep=B/'encoding.json';encoded=json.loads(ep.read_text());bankp=E/'adder_local_capacity_detours_v9_2026-10-09/step_3.json';bank={int(c):o for c,o in json.loads(bankp.read_text())['bank'].items()};metap=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(metap.read_text());q={x['connection_id']:x for x in meta['connections']};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);roles={}
for i,role in enumerate(encoded['variables'],1):
 key=(role['kind'],json.dumps(role['key']));assert key not in roles;roles[key]=i
used=set();expected=set();groups=defaultdict(int)
def v(kind,key):
 var=roles[kind,json.dumps(key)];used.add(var);return var
def emit(literals):expected.add(tuple(sorted(set(literals))))
def cardinality(xs,k,group):
 if len(xs)<=k:return
 groups[group[0]]+=1
 if k==0:
  for x in xs:emit([-x])
 elif k==1:
  for a,b in combinations(xs,2):emit([-a,-b])
 else:
  for i,x in enumerate(xs):
   emit([-x,v('PREFIX_COUNT',[group,i,1])])
   for count in range(1,min(i,k)+1):emit([-v('PREFIX_COUNT',[group,i-1,count]),v('PREFIX_COUNT',[group,i,count])])
   for count in range(2,min(i+1,k)+1):emit([-x,-v('PREFIX_COUNT',[group,i-1,count-1]),v('PREFIX_COUNT',[group,i,count])])
   if i>=k:emit([-x,-v('PREFIX_COUNT',[group,i-1,k])])
usage=defaultdict(lambda:defaultdict(set));parents=defaultdict(lambda:defaultdict(set));pathvars={}
for cid,options in bank.items():
 xs=[]
 for i,option in enumerate(options):
  x=v('PATH',[cid,i]);pathvars[f'{cid}:{i}']=x;xs.append(x);net=q[cid]['net_id'];path=option['path']
  for n,s in path:usage[n][net].add(x)
  for (u,_),(n,s) in zip(path,path[1:]):parents[net,n][u,s].add(x)
 emit(xs);cardinality(xs,1,['CID',cid])
for n,users in usage.items():
 cap=int(inv.physical.nodes[n][1])
 if len(users)<=cap:continue
 xs=[]
 for net in sorted(users):
  z=v('NET_NODE',[net,n]);xs.append(z)
  for x in users[net]:emit([-x,z])
 cardinality(xs,cap,['CAPACITY',n])
for (net,n),options in parents.items():
 if len(options)<2:continue
 xs=[]
 for u,s in sorted(options):
  y=v('NET_PARENT',[net,n,u,s]);xs.append(y)
  for x in options[u,s]:emit([-x,y])
 cardinality(xs,1,['PARENT',net,n])
assert pathvars==encoded['path_vars'];assert used==set(range(1,len(encoded['variables'])+1));assert expected=={tuple(c) for c in encoded['clauses']} and len(expected)==len(encoded['clauses'])
dim=(B/'problem.cnf').read_text().splitlines();assert dim[0]==f"p cnf {len(used)} {len(expected)}";assert {tuple(map(int,line.split()[:-1])) for line in dim[1:]}==expected and all(line.endswith(' 0') for line in dim[1:])
for p in (ep,bankp,metap,B/'problem.cnf'):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,connections=len(bank),variables=len(used),clauses=len(expected),constraint_groups=dict(groups),all_real_encoding_roles_and_clauses_rebuilt=True,status='ENCODING_VERIFIED_NOT_SOLVED',scope='Exact actual residual-bank clause reconstruction: one path per connection, distinctNET node capacity via forward prefix cardinality and sameNET parent uniqueness. No solver result; physical/modelbudget eligibility inherited from authenticated candidate inventory.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
