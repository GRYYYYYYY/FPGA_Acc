"""Trace exact relaxed critical paths without claiming native infeasibility."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,deque
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_initial_skip_global_floors_2026-10-07';rows=[]
for w,i in ((16,1),(16,2),(32,0),(32,1)):
 file=base/f'w{w}_m{i}/receipt.json'
 if not file.exists():continue
 r=json.loads(file.read_text());row=r['rows'][0];gf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';sf=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json';g=json.loads(gf.read_text());m=json.loads(mf.read_text());a=json.loads(af.read_text());seed=json.loads(sf.read_text());assert all(sha(f)==r['bindings'][str(f)] for f in (gf,mf,af,sf));adj=defaultdict(list);ind={int(n):0 for n in g['nodes']}
 for eid,e in g['edges'].items():
  if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
 q=deque(sorted(n for n in ind if not ind[n]));order=[]
 while q:
  u=q.popleft();order.append(u)
  for v,eid in adj[u]:
   ind[v]-=1
   if not ind[v]:q.append(v)
 assert len(order)==len(ind);arr={n:F(0) for n in order};back={};components={}
 for u in order:
  for v,eid in adj[u]:
   cid=a['edge_connection_ids'].get(eid)
   rr=F(row['minimum_ns'][str(cid)]) if cid is not None else F(0)
   local=F(m['external_edges'][eid]['old_local_offset_seconds'])*10**9 if cid is not None else F(0)
   primitive=F(g['edges'][eid]['max_delay_seconds'])*10**9 if cid is None else F(0)
   components[eid]=(cid,rr,local,primitive);value=arr[u]+rr+local+primitive
   if value>arr[v]:arr[v]=value;back[v]=(u,eid)
 sinks=sorted(int(n) for n,k in g['nodes'].items() if k=='SINK');worst=max(sinks,key=lambda n:arr[n]);assert arr[worst]==F(row['relaxed_cpd_ns']);n=worst;path=[]
 while n in back:
  n,eid=back[n];cid,rr,local,primitive=components[eid];path.append(dict(edge_id=eid,connection_id=cid,rr_minimum_ns=str(rr),old_local_offset_ns=str(local),primitive_ns=str(primitive),seed_expanded=(cid in seed['expanded_connection_ids']) if cid is not None else None))
 path.reverse();totals={k:sum((F(e[k]) for e in path),F(0)) for k in ('rr_minimum_ns','old_local_offset_ns','primitive_ns')};assert sum(totals.values())==arr[worst]
 rows.append(dict(width=w,index=i,receipt_sha256=sha(file),sink=worst,cpd_ns=str(arr[worst]),target_ns=row['target_ns'],critical_path=path,component_totals_ns={k:str(v) for k,v in totals.items()},retained_connections_on_relaxed_critical_path=[e['connection_id'] for e in path if e['connection_id'] is not None and not e['seed_expanded']]))
report=dict(source_sha256=sha(Path(__file__)),rows=rows,complete=len(rows)==4,scope='Exact model critical path decomposition, RR minima versus frozen old local offsets and primitive delays. Producer receipt hashes bound; native timing and full physical realization not asserted.')
(base/'critical_path_explanation.json').write_text(json.dumps(report,indent=2)+'\n');print([(r['width'],r['index'],len(r['critical_path']),r['retained_connections_on_relaxed_critical_path']) for r in rows],flush=True)
