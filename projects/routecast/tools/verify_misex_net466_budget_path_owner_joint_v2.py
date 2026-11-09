"""Independent complete-scope, original budgets, tree, preserved seed and capacity checks."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_net466_budget_path_owner_joint_v2_2026-10-07';parent=R/'experiments/misex_net466_budget_path_owner_release_v2_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());assert r['bindings']==p['bindings'];proposals=json.loads((parent/'proposals.json').read_text());options={int(n):ops for n,ops in json.loads((parent/'core_options.json').read_text()).items()};event=json.loads((out/'event.json').read_text());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);xml=ImmutableXMLAudit(graph,digest);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids']);assert len(expected)==2172 and r['required']==len(queries)==2449;core={258,384,466};memo={};states=[]
for index,a in enumerate(r['attempts']):
 assert a['index']==index and a['plan']==p['schedule'][index];plan=a['plan'];proposal=proposals[plan['proposal_index']];assert a['release']==proposal['release'] and a['extra_owners']==proposal['extra_owners'];kept={x['connection_id']:x for x in event['before_records'] if x['net_id'] not in proposal['release']};core_records={x['connection_id']:x for net,i in proposal['core_option_indices'].items() for x in options[int(net)][i]['records']};seed={**kept,**core_records};assert len(seed)==len(kept)+len(core_records);restoration={x['connection_id']:qm[x['connection_id']] for x in event['before_records'] if x['net_id'] in proposal['release'] and x['net_id'] not in core};assert set(seed)|set(restoration)==expected and not set(seed).intersection(restoration);qs=plan['queries'];assert len(qs)==len(restoration) and {q['connection_id']:q for q in qs}==restoration;assert len(plan['net_order'])==len(set(plan['net_order'])) and set(plan['net_order'])=={q['net_id'] for q in qs};assert [q['net_id'] for q in qs]==[n for n in plan['net_order'] for q in sorted((q for q in restoration.values() if q['net_id']==n),key=lambda q:q['connection_id'])];state=json.loads(Path(a['state_file']).read_text());states.append(state);records={x['connection_id']:x for x in state['records']};assert len(records)==len(state['records']) and all(records[cid]==rec for cid,rec in seed.items());assert state['failure']==a['failure'];restored=set(records)-set(seed)
 if a['failure'] is None:assert restored==set(restoration)
 else:
  fail=a['failure']['query'];assert fail in qs;assert restored=={q['connection_id'] for q in qs[:qs.index(fail)]}
 owners=defaultdict(set);parents=defaultdict(dict)
 for cid,rec in records.items():
  q=qm[cid];assert all(rec[k]==q[k] for k in ['net_id','source','sink']);floor=floors[q['source'],q['sink']];budget=max(rc.scale//10**9,(3*floor+1)//2);assert rec['floor_integer']==floor and rec['budget_integer']==budget and rec['answer']['status']=='FOUND';edges=tuple(rec['answer']['physical_edge_ids']);key=(cid,edges,rec['answer']['delay'],budget,floor)
  if key not in memo:
   assert rc.path(q['source'],q['sink'],edges)==rec['answer']['delay']<=budget;u=q['source'];used={u};incoming=[]
   for e in edges:
    arc=xml.graph.edges[e];assert arc.source==u;v=arc.sink;assert v not in used;used.add(v);incoming.append((v,(u,e)));u=v
   assert u==q['sink'];memo[key]=(used,incoming)
  used,incoming=memo[key];owners[q['net_id']].update(used)
  for v,par in incoming:assert v not in parents[q['net_id']] or parents[q['net_id']][v]==par;parents[q['net_id']][v]=par
 ledger=Counter(n for own in owners.values() for n in own);assert ledger==Counter({int(n):c for n,c in state['ledger'].items()});assert all(c<=f['capacities'][n] for n,c in ledger.items());assert state['completed_connections']==len(records) and state['required_connections']==len(expected);print('PASS restoration state',index,len(records),flush=True)
candidate=json.loads((out/'candidate.json').read_text())
if candidate is None:assert r['completed'] is None and all(x['failure'] is not None for x in states)
else:
 assert states[-1]['failure'] is None and candidate['records']==states[-1]['records'] and candidate['ledger']==states[-1]['ledger'];assert {x['connection_id'] for x in candidate['records']}==expected;assert candidate['required_connections']==len(queries) and candidate['completed_connections']==r['completed']==len(expected);assert candidate['pending_connection_ids']==sorted(set(qm)-expected);assert candidate['released_net_ids']==r['attempts'][-1]['release']
assert all(sha(k)==h for k,h in bindings.items());(out/'branch_verification_dedup.json').write_text(json.dumps(dict(bindings=bindings,states_verified=len(states),unique_physical_record_audits=len(memo),all_original_budgets_xml_tree_caps_full_release_scope_and_preserved_seed_checks_pass=True,local_solution_present=candidate is not None,scope='All failed and successful archived restoration states checked; every released NET remains required, partial branches not accepted, no native/QoR/heldout/workflow evidence.'),indent=2)+'\n');print('PASS full owner restoration',len(states),candidate is not None,flush=True)
