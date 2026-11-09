"""Snapshot-only congestion path eligibility; exclude unobserved force-reroute flags."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10';bindings=closure([Path(__file__)])
for name in ['pin_identity_audit_v1.json','common_state_projection_verification_v1.json']:
 p=D/name;v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
manifest=R/'experiments/native_manifest_scope_preflight_v1_2026-10-10/mmc.queries';assert str(manifest) in bindings
queries=defaultdict(list)
for line in manifest.read_text().splitlines():
 a=line.split()
 if a[0]=='Q':
  cid,net,pin,source,sink=map(int,a[1:]);queries[net].append((cid,pin,source,sink))
state=D/'states/round_1.tsv';assert sha(state)==bindings[str(state)];occ={};cap={};trees=defaultdict(dict);pins={}
with state.open() as f:
 for line in f:
  a=line.split()
  if a[0]=='N':n=int(a[1]);assert n not in cap;occ[n]=int(a[2]);cap[n]=int(a[3])
  elif a[0]=='T':
   net,node,parent=int(a[1]),int(a[2]),int(a[3]);assert node not in trees[net];trees[net][node]=parent
   if int(a[6])>=1:pins[net,int(a[6])]=node
assert len(cap)==904438 and len(queries)==55300 and sum(map(len,queries.values()))==115572
counts=Counter();rows=[]
for net,qs in sorted(queries.items()):
 good=bad=0;kept=set();owned=set(trees[net]);memo={}
 for cid,pin,source,sink in qs:
  assert pins[net,pin]==sink;u=sink;path=[];seen=set()
  while u!=-1:
   assert u not in seen;seen.add(u);path.append(u);u=trees[net][u]
  assert path[-1]==source
  clean=all(occ[n]<=cap[n] for n in path)
  good+=clean;bad+=not clean
  if clean:kept.update(path)
 eligible=len(qs)>=16
 counts['nets']+=1;counts['connections']+=len(qs);counts['congestion_clean_connections']+=good
 if eligible:
  counts['fanout16plus_nets']+=1;counts['fanout16plus_connections']+=len(qs);counts['fanout16plus_clean_connections']+=good;counts['fanout16plus_congested_connections']+=bad;counts['fanout16plus_clean_union_nodes']+=len(kept);counts['fanout16plus_old_union_nodes']+=len(owned);counts['fanout16plus_mixed_nets']+=good>0 and bad>0
 rows.append(dict(net=net,fanout=len(qs),threshold_eligible=eligible,clean_connections=good,congested_connections=bad,clean_union_nodes=len(kept),old_union_nodes=len(owned)))
assert all(sha(k)==h for k,h in bindings.items());out=R/'experiments/mmc_selective_tree_preflight_v1_2026-10-13/native_round1_eligibility_v1.json';assert not out.exists();out.write_text(json.dumps(dict(bindings=bindings,counts=dict(counts),pernet=rows,scope='Authenticated first-round snapshot path congestion eligibility only. Ignores unavailable force-reroute/hold decisions and nonconfigurable stubs; online earlier NET updates change occupancy. No actual retained subtree or saved search/runtime proof.'),indent=2)+'\n');print(dict(counts),flush=True)
