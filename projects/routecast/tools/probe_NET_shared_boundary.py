"""Deterministic synthetic probe; nonterminal sinks, nonnegative edge weights."""
import random,json
from pathlib import Path
from types import SimpleNamespace
from pre_route_endpoints import sha
from pressure_capacity_forecast import forecast as original
from net_shared_capacity_forecast import forecast as shared
rng=random.Random(20261006);rows=[]
for case in range(10000):
 n=16;arcs=[]
 for u in range(n):
  for v in range(1,n):
   if v!=u and rng.random()<.16:arcs.append((u,v,rng.randrange(0,8)))
 offsets=[0];dst=[];ids=[];weights=[]
 for u in range(n):
  for a,b,w in arcs:
   if a==u:dst.append(b);ids.append(len(ids));weights.append(w)
  offsets.append(len(ids))
 f={'capacities':[rng.randrange(1,4) for _ in range(n)],'row_offsets':offsets,'dest_ranks':dst,'edge_ids':ids}
 queries=[{'net_id':net,'connection_id':i,'source':source,'sink':sink} for net,source in enumerate([0,1,2]) for i,sink in enumerate(rng.sample(list(range(12,16)),4))]
 rc=SimpleNamespace(increments=weights,initial=lambda _:0,scale=10**12)
 ctx=SimpleNamespace(context=(None,'synthetic',list(range(n)),f,rc,queries))
 for soft in [True,False]:
  a=original(ctx,soft);b=shared(ctx,soft)
  equal={k:v for k,v in a.items() if k!='events'}=={k:v for k,v in b.items() if k!='events'}
  if not equal:rows.append({'case':case,'soft':soft,'original':a,'shared':b,'fields':f,'weights':weights,'queries':queries})
out=Path(__file__).resolve().parents[1]/'experiments/NET_shared_boundary_probe_2026-10-06';out.mkdir()
result={'seed':20261006,'cases':10000,'modes_per_case':2,'terminal_sinks':False,'strict_positive_edge_weights':False,'source_sha256':{n:sha(Path(__file__).parent/n) for n in ['probe_NET_shared_boundary.py','pressure_capacity_forecast.py','net_shared_capacity_forecast.py']},'mismatch_count':len(rows),'counterexamples':rows,'scope':'Small arbitrary directed graphs; empirical probe only, not proof or real-RR performance.'}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print({'mismatch_count':len(rows),'comparisons':20000})
