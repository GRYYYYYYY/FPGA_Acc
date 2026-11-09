"""All4096 directed four-vertex graphs versus mutual reachability oracle."""
import json,hashlib
from pathlib import Path
from diagnose_target_channel_release_dependencies_v2 import scc
R=Path(__file__).resolve().parents[1];D=R/'experiments/target_release_SCC_contract_v2_2026-10-20'
def main():
 D.mkdir(exist_ok=False);arcs=[(u,v) for u in range(4) for v in range(4) if u!=v]
 for mask in range(1<<len(arcs)):
  adj={u:set() for u in range(4)}
  for i,(u,v) in enumerate(arcs):
   if mask>>i&1:adj[u].add(v)
  components,ids,reverse=scc(adj);reach={}
  for start in adj:
   todo=[start];visited={start}
   while todo:
    for child in adj[todo.pop()]:
     if child not in visited:visited.add(child);todo.append(child)
   reach[start]=visited
  assert all((ids[u]==ids[v])==(v in reach[u] and u in reach[v]) for u in adj for v in adj)
 files=[Path(__file__),R/'tools/diagnose_target_channel_release_dependencies_v2.py'];(D/'verification.json').write_text(json.dumps(dict(status='ALL4096_FOUR_VERTEX_SCC_PARTITIONS_MATCH_MUTUAL_REACHABILITY',graphs=4096,bindings={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),indent=2)+'\n');print('ALL4096_FOUR_VERTEX_SCC_PARTITIONS_MATCH_MUTUAL_REACHABILITY')
if __name__=='__main__':main()
