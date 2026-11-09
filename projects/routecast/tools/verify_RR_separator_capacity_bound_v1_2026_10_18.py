"""Independent literal separators and exhaustive joint path feasibility oracle."""
import json,random,hashlib
from collections import Counter
from pathlib import Path
from RR_separator_capacity_bound_v1 import profile

def paths(n,edges,source,target):
 adj={i:[] for i in range(n)}
 for u,v in edges:adj[u].append(v)
 result=[]
 def walk(u,seen):
  if u==target:result.append(frozenset(seen));return
  for v in adj[u]:
   if v not in seen:walk(v,seen|{v})
 walk(source,{source});return result

def main():
 rng=random.Random(741013);checks=certificates=0
 for _ in range(200):
  n=6;lo=[rng.randrange(4) for _ in range(n)];hi=[a+rng.randrange(2) for a in lo];caps=[rng.randrange(1,3) for _ in range(n)];edges=[(u,v) for u in range(n) for v in range(n) if u!=v and rng.randrange(4)==0];nets={0:{0,4},1:{1,5}};p=profile(lo,hi,edges,caps,nets);joint_paths=[paths(n,edges,0,4),paths(n,edges,1,5)]
  for k in range(min(lo),max(hi)):
   boundary={i for i in range(n) if lo[i]<=k<hi[i]};side={i:-1 if hi[i]<=k else 1 if lo[i]>k else 0 for i in range(n)}
   for u,v in edges:
    if side[u]*side[v]==-1:boundary.add(v)
   assert boundary=={i for i in range(n) if p['lower'][i]<=k<p['upper'][i]}
   assert all(u in boundary or v in boundary or side[u]==side[v] for u,v in edges)
   forced={net for net,ts in nets.items() if ts&boundary or {side[t] for t in ts}=={-1,1}};row=max((r for r in p['cuts'] if r['cut_after_coordinate']<=k),key=lambda x:x['cut_after_coordinate']);assert row['separator_capacity']==sum(caps[i] for i in boundary) and row['mandatory_unique_NETs']==len(forced)
   for net in forced:
    for path in joint_paths[net]:assert path&boundary
   if len(forced)>sum(caps[i] for i in boundary):
    certificates+=1
    for a in joint_paths[0]:
     for b in joint_paths[1]:assert any(v>caps[i] for i,v in Counter(list(a)+list(b)).items())
   checks+=1
 # Two NETs must use one capacity1 spanning resource.
 p=profile([0,0,0,1,1],[0,0,1,1,1],[(0,2),(1,2),(2,3),(2,4)],[1]*5,{0:{0,3},1:{1,4}});assert p['any_capacity_infeasibility_certificate'] and p['cuts'][0]['mandatory_unique_NETs']==2 and p['cuts'][0]['separator_capacity']==1
 # A direct arc bypasses every geometric spanning node: patch its destination.
 p=profile([0,1],[0,1],[(0,1)],[1,1],{0:{0,1}});assert not p['any_capacity_infeasibility_certificate'] and p['cuts'][0]['separator_capacity']==1
 # Several sinks of the sameNET contribute one owner, not multiple connections.
 p=profile([0,0,1,1],[0,1,1,1],[(0,1),(1,2),(1,3)],[1]*4,{7:{0,2,3}});assert not p['any_capacity_infeasibility_certificate'] and p['cuts'][0]['mandatory_unique_NETs']==1
 r=Path(__file__).resolve().parents[1];out=r/'experiments/RR_separator_capacity_bound_core_v1_2026-10-18';out.mkdir();files=[Path(__file__).resolve(),r/'tools/RR_separator_capacity_bound_v1.py'];result=dict(status='literal_separator_membership_all_cut_demands_and_joint_path_capacity_oracle_pass',random_graphs=200,integer_cut_checks=checks,random_positive_cut_certificates_checked_against_all_joint_paths=certificates,direct_arc_bypass_patch_pass=True,multisink_same_NET_counted_once=True,shared_capacity_infeasibility_fixture_pass=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},scope='Small abstract directed graphs only. No real RR terminal mapping, native-failure prediction, generalization, speed or hardware claim.');(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['bindings','scope']}))
if __name__=='__main__':main()
