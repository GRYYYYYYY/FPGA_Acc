"""Old-state plus explicit budget search; target route/state is never consumed."""
import json,time
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
from class_cached_rc_endpoint_context_v1 import load_endpoints
from transaction_shared_tree_ledger_v1 import TransactionLedger
from native_bounded_wire_search_v1 import NativeBoundedSearch
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_online_failure_probe_v1_2026-10-09';D.mkdir(exist_ok=False);start=time.perf_counter();ep0=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';g,h,nodes,f,rc,_=load_endpoints(ep0);bindings=closure([Path(__file__)]);length={}
for n,node in enumerate(nodes):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[n]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
search=NativeBoundedSearch(rc,length);bindings.update(search.bindings);bindings[str(g)]=h;edge={f['edge_ids'][i]:(u,f['dest_ranks'][i],f['switch_ids'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};lookup={v:k for k,v in edge.items()};rows=[]
for step in range(1,4):
 oldep=ep0 if step==1 else E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step-1}_endpoints.json';ep=E/f'adder_tree_2L032_move_sequence_2026-10-06/step_{step}_endpoints.json';oldp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step-1}_state.json';bp=E/f'adder_legal_route_budget_fixture_v1_2026-10-09/step_{step}_budgets.json'
 for p in (oldep,ep,oldp,bp):bindings[str(p)]=sha(p)
 om=json.loads(oldep.read_text());m=json.loads(ep.read_text());assert om['graph_sha256']==m['graph_sha256']==h;assert all(sha(x['path'])==x['sha256'] for meta in (om,m) for x in meta['inputs'].values());oq={q['connection_id']:q for q in om['connections']};q={q['connection_id']:q for q in m['connections']};old={int(c):tuple(tuple(x) for x in p) for c,p in json.loads(oldp.read_text())['state'].items()};budgets={b['connection_id']:F(*b['exact_delay_s']) for b in json.loads(bp.read_text())};assert set(old)==set(q)==set(oq)==set(budgets)
 changed={c for c in q if (oq[c]['source'],oq[c]['sink'])!=(q[c]['source'],q[c]['sink'])};budgetfails=set()
 for c in set(q)-changed:
  path=old[c];ids=[lookup[u,v,s] for (u,_),(v,s) in zip(path,path[1:])]
  if F(rc.path(q[c]['source'],q[c]['sink'],ids),rc.scale)>budgets[c]:budgetfails.add(c)
 nets={q[c]['net_id'] for c in changed|budgetfails};released=sorted(c for c in q if q[c]['net_id'] in nets);candidate=TransactionLedger(old,oq,f['capacities'],length)
 for cid in released:candidate.release(cid)
 candidate.queries=q
 prior=E/'adder_online_endpoint_update_v1_2026-10-09';vp=prior/'verification.json';report=json.loads(vp.read_text());assert all(sha(p)==h for p,h in report['bindings'].items());bindings.update(report['bindings']);bindings[str(vp)]=sha(vp);doc=json.loads((prior/f'step_{step}.json').read_text())
 for event in doc['events']:
  if event['status']=='FOUND':candidate.insert(event['connection_id'],event['path'])
 failed=doc['failed_connection'];query=q[failed];net=query['net_id'];kept=set(candidate.nodes[net]);parents=dict(candidate.parents[net]);outside=Counter({n:v-int(n in candidate.nodes[net]) for n,v in candidate.occupancy.items()});value=budgets[failed]*rc.scale;probes=[]
 for mask in (0,1,2,3):
  result=search.query(query['source'],query['sink'],value.numerator//value.denominator,Counter() if mask&1 else outside,kept,{} if mask&2 else parents,1000000,sum(length.values())+1);row=dict(mask=mask,relax_capacity=bool(mask&1),relax_parents=bool(mask&2),connection_id=failed,**result)
  if result['status']=='FOUND':
   path=[(query['source'],None)];u=query['source'];owners=set();conflicts=[]
   for eid in result['physical_edge_ids']:
    source,v,sw=edge[eid];assert source==u;path.append((v,sw));u=v
    if outside[v]>=f['capacities'][v]:
     blocked={n for n,counts in candidate.nodes.items() if v in counts and n!=net};owners.update(blocked);conflicts.append(dict(node=v,owners=sorted(blocked)))
   row.update(path=path,capacity_conflicts=conflicts,blocker_nets=sorted(owners),external_old_nets=sorted(owners-nets),already_staged_nets=sorted(owners&nets))
  probes.append(row)
 out=dict(step=step,failed_connection=failed,probes=probes,paths_installed=0);p=D/f'step_{step}.json';p.write_text(json.dumps(out,indent=2)+'\n');bindings[str(p)]=sha(p);rows.append(dict(step=step,failed_connection=failed,statuses=[p['status'] for p in probes],external_old_nets=[p.get('external_old_nets',[]) for p in probes]));print(rows[-1],flush=True)
search.close();assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,component_seconds=time.perf_counter()-start,scope='Replay exact failed online candidate then budget-preserving capacity/parent relaxed searches. Diagnostic paths never installed; no global infeasibility, complete candidate/native/independent timing/gain claim.'),indent=2)+'\n')
