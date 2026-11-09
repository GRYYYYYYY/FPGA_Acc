"""Exact two-edge endpoint messages; directed physical multigraph semantics."""
from collections import defaultdict
BASE=['source_NETs','source_CIDs','source_bbox_span','sink_CIDs','sink_bbox_span']
COLUMNS=BASE+[f'forward_{h}_{name}' for h in [1,2] for name in BASE[:3]]+[f'reverse_{h}_{name}' for h in [1,2] for name in BASE[3:]]
def extract(node_ids,edges,queries,NETs):
 ids=list(node_ids);nodes=set(ids)
 if not ids or len(ids)!=len(nodes) or any(type(n) is not int for n in ids):raise ValueError('unique integer node IDs required')
 edges=list(edges);queries=list(queries)
 if any(a not in nodes or b not in nodes for a,b in edges):raise ValueError('unknown physical endpoint')
 if len({q['connection_id'] for q in queries})!=len(queries):raise ValueError('duplicate CID')
 grouped=defaultdict(list)
 for q in queries:
  if q['source'] not in nodes or q['sink'] not in nodes or q['net_id'] not in NETs:raise ValueError('unknown query identity')
  grouped[q['net_id']].append(q)
 if set(grouped)!=set(NETs):raise ValueError('complete NET incidence required')
 values={n:[0]*5 for n in ids}
 for net,qs in grouped.items():
  info=NETs[net];bbox=info['endpoint_bbox'];sources={q['source'] for q in qs}
  if len(sources)!=1 or info['source_RR'] not in sources or info['fanout']!=len(qs) or len(bbox)!=4 or any(type(x) is not int for x in bbox) or bbox[2]<bbox[0] or bbox[3]<bbox[1]:raise ValueError('NET feature/incidence mismatch')
  source=info['source_RR'];span=(bbox[2]-bbox[0]+1)+(bbox[3]-bbox[1]+1);values[source][0]+=1;values[source][1]+=len(qs);values[source][2]+=span
  for q in qs:values[q['sink']][3]+=1;values[q['sink']][4]+=span
 result={n:list(v) for n,v in values.items()}
 for forward,start,end in [(True,0,3),(False,3,5)]:
  current={n:v[start:end] for n,v in values.items()}
  for hop in [1,2]:
   nxt={n:[0]*(end-start) for n in ids}
   for a,b in edges:
    src,dst=(a,b) if forward else (b,a)
    for i,v in enumerate(current[src]):nxt[dst][i]+=v
   for n in ids:result[n].extend(nxt[n])
   current=nxt
 return result
