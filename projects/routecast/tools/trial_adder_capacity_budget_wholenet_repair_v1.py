"""One fixed CID-order pass, capacity-safe exact-budget branch replacements on all4 native states."""
import json,time
from fractions import Fraction as F
from collections import Counter
from pathlib import Path
from class_cached_rc_endpoint_context_v1 import load_endpoints
from load_complete_route_state_v1 import load_complete
from native_minrc_certificate_v4 import NativeMinRCCertificate
from incremental_shared_tree_ledger_v1 import SharedTreeLedger
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_capacity_budget_wholenet_repair_v1_2026-10-08';D.mkdir(exist_ok=False)
P=E/'adder_four_step_native_model_budgets_v1_2026-10-08/verification.json';v=json.loads(P.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());bindings={**v['bindings'],str(P):sha(P)}
ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0)
search=NativeMinRCCertificate(rc);bindings.update(search.bindings);edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
(D/'protocol.json').write_text(json.dumps(dict(order='all4 steps, ascending original violation CID, one pass, fixed all other branches/NETs',max_labels=1000000,budget_policy='unchanged archived model-baseline exact budgets',bindings=bindings),indent=2)+'\n');start=time.perf_counter();summary=[]
for step in range(4):
 ep=ep0 if step==0 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';meta=json.loads(ep.read_text());route=g.with_name('design.route') if step==0 else E/f'native_resume_all_inventory_adder_step{step}_cold_2026-10-07/first/output.route'
 state,initial,ledger=load_complete(route,meta,nodes,f,rc);prior=E/f'adder_capacity_budget_branch_repair_v1_2026-10-08/step_{step}.json';previous=json.loads(prior.read_text());bindings[str(prior)]=sha(prior);ledger=SharedTreeLedger({int(cid):path for cid,path in previous['state'].items()},ledger.queries,f['capacities'],ledger.length);budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads((E/f'adder_tree_online_move_rc_budgets_2026-10-06/step_{step}_budgets.json').read_text())};queries={q['connection_id']:q for q in meta['connections']}
 violations=previous['violation_ids'];events=[]
 nets=sorted({queries[cid]['net_id'] for cid in violations})
 for net in nets:
  cids=sorted(cid for cid,q in queries.items() if q['net_id']==net)
  outside=Counter({n:count-int(n in ledger.nodes[net]) for n,count in ledger.occupancy.items()})
  parents={};kept=set();staged={};attempts=[]
  for cid in cids:
   q=queries[cid];value=budgets[cid]*rc.scale;limit=value.numerator//value.denominator
   result=search.query(q['source'],q['sink'],limit,outside,kept,parents,1000000,1);attempts.append(dict(connection_id=cid,**result))
   if result['status']!='FOUND':break
   path=[(q['source'],None)];node=q['source']
   for eid in result['physical_edge_ids']:
    u,v,switch=edge[eid];assert u==node;path.append((v,switch));node=v
    assert v not in parents or parents[v]==(u,switch);parents[v]=(u,switch)
   staged[cid]=path;kept.update(n for n,switch in path)
  committed=len(staged)==len(cids)
  if committed:
   candidate=dict(ledger.state);candidate.update(staged)
   ledger=SharedTreeLedger(candidate,queries,f['capacities'],ledger.length)
  events.append(dict(net_id=net,connections=cids,committed=committed,attempts=attempts))
 delays=[];remaining=[]
 for cid,path in ledger.state.items():
  ids=[]
  for (u,_),(v,s) in zip(path,path[1:]):
   matches=[f['edge_ids'][i] for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if (f['dest_ranks'][i],f['switch_ids'][i])==(v,s)];assert len(matches)==1;ids.extend(matches)
  delay=F(rc.path(queries[cid]['source'],queries[cid]['sink'],ids),rc.scale);ok=delay<=budgets[cid]
  delays.append(dict(connection_id=cid,delay_seconds=str(delay),budget_seconds=str(budgets[cid]),budget_pass=ok))
  if not ok:remaining.append(cid)
 demand=Counter(n for used in ledger.nodes.values() for n in used);assert demand==ledger.occupancy and all(demand[n]<=f['capacities'][n] for n in demand)
 out=D/f'step_{step}.json';out.write_text(json.dumps(dict(events=events,state={str(cid):path for cid,path in ledger.state.items()},rows=sorted(delays,key=lambda x:x['connection_id']),violation_ids=sorted(remaining),node_occupancy={str(n):c for n,c in demand.items()}),indent=2)+'\n');bindings[str(out)]=sha(out)
 row=dict(step=step,initial_violations=len(violations),repaired=len(violations)-len(remaining),remaining_violations=len(remaining),committed_nets=sum(e['committed'] for e in events),status_counts=dict(Counter(a['status'] for e in events for a in e['attempts'])),overflow_units=0);summary.append(row);print(row,flush=True)
search.close();assert all(sha(f)==h for f,h in bindings.items())
for name in ('trial_adder_capacity_budget_branch_repair_v1.py','native_minrc_certificate_v4.py','load_complete_route_state_v1.py','class_cached_rc_endpoint_context_v1.py','incremental_shared_tree_ledger_v1.py'):
 p=R/'tools'/name;bindings[str(p)]=sha(p)
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=summary,component_seconds=time.perf_counter()-start,scope='Capacity-safe per-branch one-pass repair of all native budget violations, fixed remaining current branches. Conditional search failures do not prove global joint infeasibility; LABEL_LIMIT incomplete. Atomic wholeNET all-budget completion only, untouched on failure. No native serialization/reload, independent final Fraction validation, wire/CPD/gain or user-clock acceptance.'),indent=2)+'\n')
