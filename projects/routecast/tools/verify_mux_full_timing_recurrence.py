"""Recompute complete combinational setup arrival recurrence from native echo."""
import json,re
from collections import defaultdict,deque
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert len(r['rows'])==3;rows=[]
for row in r['rows']:
 w=row['width'];assert row['exit_code']==0 and row['mismatches']==row['fixups']==0;assert all(sha(p)==h for p,h in row['files'].items());work=out/f'w{w}/canonical';file=work/'timing_graph.analysis.echo';text=file.read_text();nodes={int(n):kind for n,kind in re.findall(r'^ node: (\d+) \\\n  type: (\w+)',text,re.M)};assert set(nodes.values())<= {'SOURCE','SINK','IPIN','OPIN'}
 raw=re.findall(r'^ edge: (\d+) \\\n  type: (\w+) \\\n  src_node: (\d+) \\\n  sink_node: (\d+) \\\n  disabled: (true|false)',text,re.M);edges={int(e):(int(u),int(v),kind,disabled=='true')for e,kind,u,v,disabled in raw};delays={int(e):Decimal(d)for e,d in re.findall(r'^ edge: (\d+) min_delay: \S+ max_delay: (\S+)',text,re.M)};assert set(edges)==set(delays);arrivals={int(n):Decimal(t)for n,t in re.findall(r'^ type: SETUP_DATA_ARRIVAL node: (\d+) launch_domain: 0 capture_domain: -?\d+ time: (\S+)',text,re.M)};assert set(arrivals)==set(nodes);assert all(arrivals[n]==0 for n,k in nodes.items()if k=='SOURCE')
 adj=defaultdict(list);indeg={n:0 for n in nodes}
 for e,(u,v,kind,disabled)in edges.items():
  assert u in nodes and v in nodes and delays[e]>=0
  if not disabled:adj[u].append((v,e));indeg[v]+=1
 queue=deque(sorted(n for n in nodes if indeg[n]==0));a={n:Decimal(0)for n in queue};hops={n:0 for n in queue};ordered=[]
 while queue:
  u=queue.popleft();ordered.append(u)
  for v,e in adj[u]:
   nd=a[u]+delays[e]
   if v not in a or nd>a[v]:a[v]=nd
   hops[v]=max(hops.get(v,0),hops[u]+1);indeg[v]-=1
   if indeg[v]==0:queue.append(v)
 assert len(ordered)==len(nodes)
 errors={n:abs(a[n]-arrivals[n])*10**9 for n in nodes};assert all(error<=Decimal('0.000011')*(hops[n]+1)for n,error in errors.items());sinks=[n for n,k in nodes.items()if k=='SINK'];assert len(sinks)==w*8;cpd=max(a[n]for n in sinks)*10**9;assert abs(cpd-Decimal(str(row['cpd_ns'])))<Decimal('0.00005')
 graph=out/f'w{w}_timing_graph.json';graph.write_text(json.dumps(dict(nodes=nodes,edges={str(e):dict(source=u,sink=v,type=k,disabled=d,max_delay_seconds=str(delays[e]))for e,(u,v,k,d)in edges.items()},recomputed_arrival_seconds={str(n):str(v)for n,v in a.items()},scope='Complete currentcombinationalnativegraph; 6-significant-digit echo values. Atom/RR identity mapping still pending.'),indent=2)+'\n');rows.append(dict(width=w,nodes=len(nodes),edges=len(edges),sinks=len(sinks),recomputed_cpd_ns=str(cpd),native_cpd_ns=row['cpd_ns'],maximum_node_arrival_error_ns=str(max(errors.values())),echo_sha256=sha(file),graph_sha256=sha(graph)));print(rows[-1],flush=True)
(out/'recurrence_verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Independent complete DAG maxplus reconstruction matches original nativeSTA nodes/CPD within explicitly echoed precision; not generic clocks/latches/timingexceptions support or movedpredictionvalidation.'),indent=2)+'\n')
