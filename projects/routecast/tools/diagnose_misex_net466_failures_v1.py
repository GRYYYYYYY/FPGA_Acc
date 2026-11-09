"""Full reverse minima under kept capacities and exact failed branch bans."""
import sys,json,heapq,struct
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
parent=R/'experiments/misex_window_witness_guided_joint_v34_2026-10-07';rp=parent/'receipt.json';r=json.loads(rp.read_text());out=R/'experiments/misex_net466_failure_minima_v1_2026-10-07';out.mkdir();bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='All saved LOW_LEVEL_FAILED queries, original graph scalar RC, exact kept capacity and branch bans; ignores single-parent tree restrictions. Exact ordinary minima do not establish native infeasibility or overall completeness.'))+'\n');event=json.loads((parent/'event.json').read_text());_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={e:s for s,e in enumerate(f['edge_ids'])};owners=defaultdict(set)
for rec in event['before_records']:owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[e]] for e in rec['answer']['physical_edge_ids'])
reverse=[[] for _ in nodes]
for u in range(len(nodes)):
 for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):reverse[f['dest_ranks'][s]].append((u,s))
INF=(1<<64)-1;rows=[]
for directory in sorted(parent.glob('attempt*_branch*')):
 bp=directory/'branch.json';meta=json.loads(bp.read_text());b=meta['branch'];bindings[str(bp)]=sha(bp)
 for netstr,failure in b['failures'].items():
  if failure is None:continue
  q=failure['query'];net=int(netstr);assert net==q['net_id'];bans={node for owner,node in b['constraints'] if owner==net};occupancy=Counter(node for owner,ns in owners.items() if owner not in meta['released_net_ids'] and owner!=net for node in ns);allowed=[i not in bans and f['capacities'][i]>occupancy[i] for i in range(len(nodes))];src,sink=q['source'],q['sink'];dist={};back={};queue=[]
  if allowed[sink]:dist[sink]=0;queue=[(0,sink)]
  while queue:
   d,v=heapq.heappop(queue)
   if dist[v]!=d:continue
   for u,s in reverse[v]:
    if not allowed[u]:continue
    nd=d+rc.increments[s]
    if nd<dist.get(u,INF):dist[u]=nd;back[u]=(v,s);heapq.heappush(queue,(nd,u))
  minimum=None if not allowed[src] or src not in dist else rc.initial(src)+dist[src];path=[]
  if minimum is not None:
   u=src;seen=set()
   while u!=sink:assert u not in seen;seen.add(u);u,s=back[u];path.append(f['edge_ids'][s])
   assert rc.path(src,sink,path)==minimum
  stem=directory.name+'_net'+netstr;df=out/(stem+'_distance.bin');af=out/(stem+'_allowed.bin');df.write_bytes(b''.join(struct.pack('<Q',dist.get(i,INF)) for i in range(len(nodes))));af.write_bytes(bytes(allowed));rows.append(dict(branch_file=str(bp),net=net,query=q,release=meta['released_net_ids'],bans=sorted(bans),budget=failure['budget_integer'],minimum_integer=minimum,physical_edge_ids=path,ordinary_budget_feasible=minimum is not None and minimum<=failure['budget_integer'],distance_file=str(df),distance_sha256=sha(df),allowed_file=str(af),allowed_sha256=sha(af)));print(stem,minimum,failure['budget_integer'],rows[-1]['ordinary_budget_feasible'],flush=True)
assert all(sha(k)==h for k,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),bindings=bindings,rows=rows),indent=2)+'\n')
