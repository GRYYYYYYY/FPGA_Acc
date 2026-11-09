"""Endpoint tree identity census; cannot distinguish retention from reconstruction."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10'
p=D/'common_state_projection_verification_v1.json';proof=json.loads(p.read_text());assert proof['all21rounds_common_state_fields_exactly_equal'];assert all(sha(k)==h for k,h in proof['bindings'].items());bindings={**closure([Path(__file__)]),**proof['bindings'],str(p):sha(p)}
def trees(i):
 p=D/'states'/f'round_{i}.tsv';assert sha(p)==bindings[str(p)];t=defaultdict(dict)
 with p.open() as f:
  for line in f:
   a=line.split()
   if a[0]=='T':
    net,node=int(a[1]),int(a[2]);assert node not in t[net];t[net][node]=tuple(a[3:5])
 return t
old,new=trees(1),trees(2);assert set(old)==set(new);counts=Counter();pernet=[]
for n in sorted(old):
 a,b=old[n],new[n];same=sum(node in b and b[node]==edge for node,edge in a.items());counts['nets']+=1;counts['same_whole_tree']+=a==b;counts['changed_whole_tree']+=a!=b;counts['old_nodes']+=len(a);counts['new_nodes']+=len(b);counts['same_node_parent_switch']+=same;counts['removed_nodes']+=len(a.keys()-b.keys());counts['added_nodes']+=len(b.keys()-a.keys());counts['changed_parent_switch']+=sum(a[x]!=b[x] for x in a.keys()&b.keys());counts['changed_nets_with_common_nodes']+=a!=b and same>0
 pernet.append(dict(net=n,old_nodes=len(a),new_nodes=len(b),same_node_parent_switch=same,whole_tree_equal=a==b))
assert all(sha(k)==h for k,h in bindings.items())
out=D/'round12_tree_change_diagnosis_v1.json';assert not out.exists();out.write_text(json.dumps(dict(bindings=bindings,counts=dict(counts),pernet=pernet,scope='Authenticated iteration endpoint node-parent-switch identity only. Equal trees or common branches may have been rebuilt; no intermediate prune-retention or search-count proof.'),indent=2)+'\n');print(dict(counts),flush=True)
