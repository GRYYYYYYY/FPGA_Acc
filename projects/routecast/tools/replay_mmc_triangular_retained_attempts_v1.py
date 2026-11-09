"""Replay every retained attempt under recorded immutable per-round prices; no model changes."""
import json,sys,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from class_cached_rc_endpoint_context_v1 import load_endpoints
from hybrid_bidirectional_search_v1 import Search
D=R/'experiments/mmc_triangular_retained_attempt_replay_v1_2026-10-09';assert not D.exists()
base=R/'experiments/mmc_triangular_span_v9_2026-10-09';model=base/'model'
bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
def auth(r):
 for field in ['bindings','files']:
  for p,h in r.get(field,{}).items():assert sha(p)==h;bindings[p]=h
proof=load(base/'verification.json');assert proof['complete_candidate_physical_and_events_pass'];auth(proof)
protocol=load(base/'protocol.json');auth(protocol);endpoint=Path(protocol['endpoint']);assert sha(endpoint)==protocol['endpoint_sha256']
r=load(model/'receipt.json');auth(r)
physical=load(model/'initial_physical_verification.json');auth(physical);assert physical['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
initial=load(model/'initial.json');floor_records={x['connection_id']:x for x in initial['records']};states=[load(model/'round0.json'),load(model/'round1.json')]
D.mkdir();(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='All retained events, same original graph and frozen recorded prices/50ps unit, exact unchanged hybrid search. Archived model states not updated. Diagnostic replay only, not new candidate/native/heldout/workflow speed evidence.'),indent=2)+'\n')
begin=time.perf_counter();graph,digest,nodes,fields,rc,queries=load_endpoints(endpoint);assert digest==initial['graph_sha256'];groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
assert len(queries)==len(floor_records)==115572
binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';search=Search(fields,rc,binary);load_seconds=time.perf_counter()-begin
weight=load(model/'protocol.json')['price_unit_integer'];assert weight==rc.scale//(20*10**9)
slots={eid:i for i,eid in enumerate(fields['edge_ids'])};rows=[];reasons=Counter();failed_ids=set();attempted_connections=0
for index,roundrow in enumerate(r['rounds']):
 prices={int(n):p for n,p in states[index]['prices'].items()};search.prepare(prices,weight);events=[e for e in roundrow['events'] if e['status']=='RETAIN_BUDGET_OR_UNREACHABLE'];count=0
 for event in events:
  qs=sorted(groups[event['net_id']],key=lambda q:q['connection_id']);src=qs[0]['source'];assert all(q['source']==src for q in qs)
  raw,parents,settled=search.search(src,{q['sink'] for q in qs});bad=[];attempts=[]
  for q in qs:
   witness=floor_records[q['connection_id']];assert all(witness[k]==q[k] for k in q)
   assert rc.path(src,q['sink'],witness['answer']['physical_edge_ids'])==witness['answer']['delay']<=witness['budget_integer']
   attempted_connections+=1;budget=witness['budget_integer']
   if q['sink'] not in settled:
    bad.append(q['connection_id']);reasons['not_settled']+=1;attempts.append(dict(connection_id=q['connection_id'],reason='NOT_SETTLED',budget=budget,feasible_initial_delay=witness['answer']['delay']));continue
   u=q['sink'];path=[];seen={u}
   while u!=src:
    previous,slot=parents[u];assert fields['row_offsets'][previous]<=slot<fields['row_offsets'][previous+1] and fields['dest_ranks'][slot]==u
    path.append(fields['edge_ids'][slot]);u=previous;assert u not in seen;seen.add(u)
   path.reverse();delay=rc.path(src,q['sink'],path);assert delay==raw[q['sink']]
   excess=max(0,delay-budget)
   if excess:bad.append(q['connection_id']);failed_ids.add(q['connection_id']);reasons['raw_RC_above_budget']+=1
   else:reasons['budget_safe_connection_in_retained_NET']+=1
   attempts.append(dict(connection_id=q['connection_id'],reason='RAW_RC_ABOVE_BUDGET' if excess else 'BUDGET_SAFE_IN_RETAINED_NET',raw_RC=delay,budget=budget,excess=excess,feasible_initial_delay=witness['answer']['delay'],physical_edge_ids=path))
  assert bad==event['failed_connection_ids'],(index,event['net_id'],bad,event['failed_connection_ids'])
  rows.append(dict(round=index,net_id=event['net_id'],epoch=event['old_epoch'],failed_connection_ids=bad,attempts=attempts));count+=1
 print('PASS complete retained round',index,count,flush=True)
search.close();assert len(rows)==2192 and reasons['not_settled']==0
assert all(sha(k)==h for k,h in bindings.items())
f=D/'attempts.json';f.write_text(json.dumps(rows)+'\n');bindings[str(f)]=sha(f)
summary=dict(bindings=bindings,all_retained_failed_ID_lists_exactly_replayed=True,all_failed_connections_have_authenticated_initial_budget_feasible_paths=True,retained_events=len(rows),reasons=dict(reasons),unique_failed_connection_ids=len(failed_ids),attempted_connections=attempted_connections,graph_context_seconds=load_seconds,local_replay_seconds=time.perf_counter()-begin,scope='Diagnostic unchanged-search replay under recorded prices, with RC reconstruction and original initial paths already covered by complete independent XML/Fraction audit. Not a second independent shortest-path algorithm/weighted optimality proof, infeasibility proof, replacement model, native legality or full-workflow timing. Paths serialized for separate original XML audit.')
(D/'receipt.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k!='bindings'},indent=2),flush=True)
