"""Separate frozen retained paths from global cold-route timing transfer."""
import json
from pathlib import Path
from fractions import Fraction as F
from collections import defaultdict,deque
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_w8m1_rejection_diagnosis_2026-10-06';out.mkdir();af=ROOT/'experiments/mux_allfanin_budgets_2026-10-06/w8_m1.json';sf=ROOT/'experiments/mux_full_cohort_cold_lifecycle_2026-10-06/mux_w8_m1_0/accepted_state.json';tf=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/w8_timing_graph.json';mf=ROOT/'experiments/mux_full_timing_rr_2026-10-06/w8.json';a=json.loads(af.read_text());snapshot=json.loads(sf.read_text());tg=json.loads(tf.read_text());mapping=json.loads(mf.read_text());assert sha(tf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];floor={int(k):F(v) for k,v in a['floor_ns'].items()};cold={r['connection_id']:F(r['answer']['delay']*10**9,snapshot['scale']) for r in snapshot['records']};assert set(floor)==set(cold);affected=set(a['affected']['affected_complete_net_connection_ids']);adj=defaultdict(list);ind={int(n):0 for n in tg['nodes']}
for eid,e in tg['edges'].items():
 if not e['disabled']:adj[e['source']].append((e['sink'],eid));ind[e['sink']]+=1
queue=deque(n for n in ind if not ind[n]);order=[]
while queue:
 u=queue.popleft();order.append(u)
 for v,eid in adj[u]:
  ind[v]-=1
  if not ind[v]:queue.append(v)
assert len(order)==len(ind)
def evaluate(b):
 arrival={n:F(0) for n in order};back={}
 for u in order:
  for v,eid in adj[u]:
   delay=b[a['edge_connection_ids'][eid]]+F(mapping['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9;value=arrival[u]+delay
   if value>arrival[v]:arrival[v]=value;back[v]=(u,eid)
 worst=max((int(n) for n,k in tg['nodes'].items() if k=='SINK'),key=lambda n:arrival[n]);path=[];n=worst
 while n in back:n,eid=back[n];path.append(eid)
 return dict(cpd_ns=str(arrival[worst]),worst_sink=worst,path_edge_ids=list(reversed(path)),arrival_ns={str(n):str(v) for n,v in arrival.items()})
vectors=dict(original_floor=floor,cold_all=cold,floor_affected_cold_retained={cid:floor[cid] if cid in affected else cold[cid] for cid in floor},cold_affected_old_retained={cid:cold[cid] if cid in affected else floor[cid] for cid in floor});results={name:evaluate(vector) for name,vector in vectors.items()};assert F(results['original_floor']['cpd_ns'])==F(a['model_floor_cpd_ns']);changes=[dict(connection_id=cid,old_retained_ns=str(floor[cid]),cold_ns=str(cold[cid]),difference_ns=str(cold[cid]-floor[cid])) for cid in sorted(set(floor)-affected) if cold[cid]!=floor[cid]];affected_below_floor=[cid for cid in affected if cold[cid]<floor[cid]]
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={str(f):sha(f) for f in (af,sf,tf,mf)},target_ns=a['target_cpd_ns'],vectors_ns={name:{str(cid):str(v) for cid,v in b.items()} for name,b in vectors.items()},results=results,changed_retained_connections=changes,cold_affected_below_diagnostic_floor=affected_below_floor,scope='Controlled old-DAG transfer, preserving old local/internal/primitive delays. Cold baseline reroutes all NETs, incremental floor freezes unaffected native paths. Native mapping/model disagreement remains possible until model result compared to independent native CPD.'),indent=2)+'\n');print({name:float(F(v['cpd_ns'])) for name,v in results.items()});print('changed retained',len(changes),'affected below floor',affected_below_floor)
