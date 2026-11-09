"""Independent compact-context materialization, RC/tree/caps and price history audit."""
import sys,json,hashlib
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_net466_expanded_negotiation_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);xml=ImmutableXMLAudit(graph,digest);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};seed=json.loads((out/'seed.json').read_text());seedmap={x['connection_id']:x for x in seed};assert len(seedmap)==len(seed);pp=R/'experiments/misex_net466_budget_path_owner_release_v3_2026-10-07';event=json.loads((out/'event.json').read_text());assert p['protected_connection_ids']==json.loads((pp/'protocol.json').read_text())['protected_connection_ids'];assert len(r['branches'])<=32;proposal=json.loads((pp/'proposals.json').read_text())[3];options=json.loads((pp/'core_options.json').read_text());expectedseed=[x for x in event['before_records'] if x['net_id'] not in proposal['release'] or x['connection_id'] in p['protected_connection_ids']]+[x for n,i in proposal['core_option_indices'].items() for x in options[n][i]['records']];assert seed==expectedseed;expected={x['connection_id'] for x in event['before_records']}|set(event['selection']['requested_connection_ids']);groups={int(n):qs for n,qs in p['groups'].items()};assert sum(len(qs) for qs in groups.values())+len(seed)==len(expected)==2172;assert {q['connection_id'] for qs in groups.values() for q in qs}==expected-set(seedmap);spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];memo={};history=Counter();states=0;lastmerged=None
def audit(records):
 owners=defaultdict(set);parents=defaultdict(dict);ids=set()
 for rec in records:
  cid=rec['connection_id'];assert cid not in ids;ids.add(cid);q=qm[cid];assert all(q[k]==rec[k] for k in ['net_id','source','sink']);floor=floors[q['source'],q['sink']];budget=max(rc.scale//10**9,(3*floor+1)//2);assert rec['floor_integer']==floor and rec['budget_integer']==budget;path=tuple(rec['answer']['physical_edge_ids']);key=(cid,path,rec['answer']['delay'])
  if key not in memo:
   assert rc.path(q['source'],q['sink'],path)==rec['answer']['delay']<=budget;u=q['source'];used={u};incoming=[]
   for edge in path:arc=xml.graph.edges[edge];assert arc.source==u and arc.sink not in used;incoming.append((arc.sink,(u,edge)));u=arc.sink;used.add(u)
   assert u==q['sink'];memo[key]=(used,incoming)
  used,incoming=memo[key];owners[q['net_id']].update(used)
  for v,parent in incoming:assert v not in parents[q['net_id']] or parents[q['net_id']][v]==parent;parents[q['net_id']][v]=parent
 return Counter(n for own in owners.values() for n in own)
assert all(c<=f['capacities'][n] for n,c in audit(seed).items())
for i,branch in enumerate(r['branches']):
 folder=out/f'round{i}';assert branch['index']==i and branch==json.loads((folder/'branch.json').read_text());merged=dict(seedmap);complete=True;netfiles=sorted(folder.glob('net*.json'),key=lambda p:int(p.stem[3:]));nets=[int(x.stem[3:]) for x in netfiles];assert nets==sorted(groups)[:len(nets)]
 for net,file in zip(nets,netfiles):
  state=json.loads(file.read_text());assert state['seed_file']==str(out/'seed.json');new=state['records'];assert all(x['net_id']==net and x['connection_id'] not in seedmap for x in new);qs=groups[net];assert all(q==qm[q['connection_id']] for q in qs);assert state['failure']==branch['failures'][str(net)];want=qs if state['failure'] is None else qs[:qs.index(state['failure']['query'])];assert {x['connection_id'] for x in new}=={q['connection_id'] for q in want};assert state['completed_connections']==len(seed)+len(new) and state['required_connections']==len(seed)+len(qs);ledger=audit(seed+new);assert ledger==Counter({int(n):c for n,c in state['ledger'].items()}) and all(c<=f['capacities'][n] for n,c in ledger.items());weighted=list(spans)
  for n,count in history.items():weighted[n]+=count*(8+hashlib.sha256(f'routecast-history-dither-v1:{net}:{n}'.encode()).digest()[0]%8)
  assert hashlib.sha256(','.join(map(str,weighted)).encode()).hexdigest()==branch['history_price_sha256'][str(net)];states+=1
  if state['failure'] is not None:complete=False;assert net==nets[-1]
  for rec in new:assert rec['connection_id'] not in merged;merged[rec['connection_id']]=rec
 if complete and len(nets)==len(groups):
  assert set(merged)==expected;ledger=audit(list(merged.values()));overuse={str(n):c-f['capacities'][n] for n,c in ledger.items() if c>f['capacities'][n]};assert branch['overuse_by_node']==overuse and branch['conflict_count']==len(overuse);assert branch['status']==('NEGOTIATED_OVERUSE' if overuse else 'FOUND_JOINT_BATCH');history.update({int(n):c for n,c in overuse.items()});lastmerged=merged
 else:assert branch['status']=='LOW_LEVEL_FAILED'
 print('PASS negotiated round',i,branch['status'],flush=True)
candidate=json.loads((out/'candidate.json').read_text())
if candidate is None:assert r['completed'] is None
else:assert r['branches'][-1]['status']=='FOUND_JOINT_BATCH' and {x['connection_id']:x for x in candidate['records']}==lastmerged;assert Counter({int(n):c for n,c in candidate['ledger'].items()})==audit(candidate['records']);assert candidate['pending_connection_ids']==sorted(set(qm)-expected);assert candidate['required_connections']==r['required']==len(queries) and candidate['completed_connections']==r['completed']==2172
assert all(sha(k)==h for k,h in bindings.items());(out/'branch_verification_dedup.json').write_text(json.dumps(dict(bindings=bindings,rounds_verified=len(r['branches']),compact_states_materialized_and_verified=states,all_xml_rc_tree_local_capacity_complete_scope_and_history_checks_pass=True,local_solution_present=candidate is not None,scope='Reconstruct every compact state with exact immutable seed; independent complete round overuse/history audit. No partial/drop commit or global/native/QoR/workflow proof.'),indent=2)+'\n');print('PASS expanded negotiation',states,flush=True)
