"""Diagnostic graph reachability only; never commits or evaluates a candidate route."""
from pathlib import Path
import struct,csv,json,hashlib,collections,time
R=Path(__file__).resolve().parents[1];W=R/'work';O=W/'additional_parent_failure_localization_20261021'
def main():
 refs={}
 def read(p):
  raw=p.read_bytes();refs[str(p)]=hashlib.sha256(raw).hexdigest();return raw
 root=W/'additional_circuit_native_costs_20261020/cases/seq_seed1';parent=W/'additional_circuit_frozen_parents_20261020/parents/seq_seed1'
 nodes=read(root/'input.nodes');edges=read(root/'input.edges');resources=read(parent/'route.resources');count=len(nodes)//8;sink=142142
 pins=set()
 for n,(begin,size,_) in enumerate(struct.iter_unpack('<IHH',nodes)):
  if any(struct.unpack_from('<I',edges,8*(begin+i))[0]==sink for i in range(size)):pins.add(n)
 free={n for n in pins if struct.unpack_from('<HH',resources,16*n)[0]==0};trees={53:set(),156:set()};roots={}
 for row in csv.DictReader(read(parent/'route.route_trees.csv').decode().splitlines()):
  net=int(row['net_id'])
  if net in trees:trees[net].update([int(row['source']),int(row['parent']),int(row['child'])]);roots[net]=int(row['source'])
 rows=[]
 for net,own in trees.items():
  visited=bytearray(count);q=collections.deque();reached=set();expanded=0;started=time.monotonic_ns()
  # Existing tree nodes are anchors; every newly visited node must have capacity after removing this net's existing usage.
  for n in own:visited[n]=1;q.append(n)
  while q and reached!=free:
   n=q.popleft();expanded+=1;begin,size,_=struct.unpack_from('<IHH',nodes,n*8)
   for i in range(size):
    dst=struct.unpack_from('<I',edges,(begin+i)*8)[0]
    if visited[dst]:continue
    occ,cap=struct.unpack_from('<HH',resources,dst*16);residual=occ-int(dst in own and dst!=roots[net])
    if residual>=cap:continue
    visited[dst]=1;q.append(dst)
    if dst in free:reached.add(dst)
  rows.append(dict(net=net,anchors=len(own),free_predecessors=len(free),reachable_free_predecessors=len(reached),reachable_ids=sorted(reached),expanded=expanded,exhausted=not q,wall_ns=time.monotonic_ns()-started))
 read(Path(__file__).resolve())
 result=dict(status='static_other_net_occupancy_reachability_probe_complete',rows=rows,source_sha256=refs,scope='Reachability from all existing tree anchors with other-net final occupancy fixed and per-node capacity admission. Does not enforce hierarchy/corridor selection, native pin identity, edge-specific timing, legal tree substitution or quality; no route submitted or cohort outcome changed.',research_complete=False)
 target=O/'static_IPIN_reachability.json';assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
