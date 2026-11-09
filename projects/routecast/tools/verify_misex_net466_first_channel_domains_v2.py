"""Independent all-arc reverse lower bounds, FIFO prefix reachability and Hall cuts."""
import sys,json,struct,itertools
from pathlib import Path
from collections import defaultdict,Counter,deque
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_first_channel_domains_v2_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());_,_,nodes,f,rc,queries=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');e=json.loads((R/'experiments/misex_net466_extra_owner_joint_v13_2026-10-07/event.json').read_text());release=set(r['release']);slots={edge:i for i,edge in enumerate(f['edge_ids'])};querymap={q['connection_id']:q for q in queries};owners=defaultdict(set);parents=defaultdict(dict);groups=defaultdict(list)
for rec in e['before_records']:
 q=querymap[rec['connection_id']];assert all(rec[k]==q[k] for k in ['net_id','source','sink']);assert rc.path(rec['source'],rec['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=rec['source'];used={u}
 for edge in rec['answer']['physical_edge_ids']:
  s=slots[edge];assert f['row_offsets'][u]<=s<f['row_offsets'][u+1];v=f['dest_ranks'][s];parent=(u,edge);assert v not in parents[rec['net_id']] or parents[rec['net_id']][v]==parent;parents[rec['net_id']][v]=parent;u=v;used.add(v)
 if rec['net_id'] not in release:owners[rec['net_id']].update(used)
 else:groups[rec['net_id']].append(q)
for q in e['selection']['queries']:groups[q['net_id']].append(q)
selected={min(qs,key=lambda q:q['connection_id'])['connection_id']:min(qs,key=lambda q:q['connection_id']) for qs in groups.values()};selected.update({q['connection_id']:q for q in e['selection']['queries']})
for row in json.loads((R/'experiments/misex_net466_failure_minima_v8_2026-10-07/receipt.json').read_text())['rows']:
 q=row['query']
 if q['net_id'] in groups:selected[q['connection_id']]=q
assert {row['query']['connection_id'] for row in r['rows']}==set(selected);occupancy=Counter(n for own in owners.values() for n in own);allowed=bytes(f['capacities'][n]>occupancy[n] for n in range(len(nodes)));assert (out/'allowed.bin').read_bytes()==allowed;channel=[n.get('type') in ('CHANX','CHANY') for n in nodes];floors={(row['source'],row['sink']):row['minimum_integer'] for row in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};INF=(1<<64)-1;checks=0
for row in r['rows']:
 q=row['query'];assert q==selected[q['connection_id']] and q['net_id']==row['net'];source,sink=q['source'],q['sink'];budget=max(rc.scale//10**9,(3*floors[source,sink]+1)//2);assert row['budget']==budget and not channel[source];p=Path(row['reverse_file']);assert sha(p)==row['reverse_sha256'];d=struct.unpack('<'+str(len(nodes))+'Q',p.read_bytes());assert d[sink]==0 if allowed[sink] else all(v==INF for v in d)
 for u in range(len(nodes)):
  if not allowed[u]:assert d[u]==INF;continue
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s]
   if allowed[v] and d[v]!=INF:assert d[u]!=INF and d[u]<=rc.increments[s]+d[v];checks+=1
 prefix={source:rc.initial(source)} if allowed[source] else {};queue=deque(prefix);first={}
 while queue:
  u=queue.popleft()
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][s];candidate=prefix[u]+rc.increments[s]
   if not allowed[v] or candidate>budget:continue
   if channel[v]:first[v]=min(first.get(v,INF),candidate)
   elif candidate<prefix.get(v,INF):prefix[v]=candidate;queue.append(v)
 expected=sorted(v for v,c in first.items() if d[v]!=INF and c+d[v]<=budget);assert row['first_channel_domain']==expected and row['no_channel_path']==(sink in prefix)
active=defaultdict(list)
for row in r['rows']:
 if not row['no_channel_path']:active[row['net']].append(row)
cuts=[]
for choice in itertools.product(*([None,*active[net]] for net in sorted(active))):
 subset=[row for row in choice if row is not None]
 if not subset:continue
 union=set(n for row in subset for n in row['first_channel_domain']);capacity=sum(f['capacities'][n]-occupancy[n] for n in union)
 if capacity<len(subset):cuts.append(dict(nets=[row['net'] for row in subset],query_ids=[row['query']['connection_id'] for row in subset],nodes=sorted(union),residual_capacity=capacity,required_distinct_nets=len(subset)))
assert cuts==r['hall_cuts'];assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,queries_verified=len(r['rows']),all_allowed_arc_checks=checks,hall_cuts_verified=len(cuts),scope='Sound necessary superset domains and exact finite Hall comparisons under fixed kept/caps/original budgets. Passing no-cut is inconclusive, no native/global or full workflow proof.'),indent=2)+'\n');print('PASS first-channel domains',len(r['rows']),checks,len(cuts))
