"""Independent original XML/RC complete core and conservative owner-release proof."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_net466_budget_path_owner_release_v2_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);xml=ImmutableXMLAudit(graph,digest);qm={q['connection_id']:q for q in queries};floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};event=json.loads((out/'event.json').read_text());groups=defaultdict(set);nodeowners=defaultdict(set);before=defaultdict(list);cut=p['cut_nodes'];core=p['core_nets'];release=p['release'];assert core==[258,384,466] and release==[24,113,157,165,180,258,331,334,384]
def own(records):
 parents=defaultdict(dict);owners=defaultdict(set);cids=set()
 for rec in records:
  cid=rec['connection_id'];assert cid not in cids;cids.add(cid);q=qm[cid];assert all(rec[k]==q[k] for k in ['net_id','source','sink']);floor=floors[q['source'],q['sink']];assert rec['floor_integer']==floor and rec['budget_integer']==max(rc.scale//10**9,(3*floor+1)//2);assert rc.path(q['source'],q['sink'],rec['answer']['physical_edge_ids'])==rec['answer']['delay']<=rec['budget_integer'];u=q['source'];owners[q['net_id']].add(u);seen={u}
  for edge in rec['answer']['physical_edge_ids']:
   arc=xml.graph.edges[edge];assert arc.source==u;v=arc.sink;assert v not in seen;seen.add(v);incoming=(u,edge);assert v not in parents[q['net_id']] or parents[q['net_id']][v]==incoming;parents[q['net_id']][v]=incoming;owners[q['net_id']].add(v);u=v
  assert u==q['sink']
 return owners
assert p['protected_original_nets']==[88];original_owners=own(event['before_records']);assert all(c<=f['capacities'][n] for n,c in Counter(n for nodeset in original_owners.values() for n in nodeset).items())
for rec in event['before_records']:
 before[rec['net_id']].append(rec)
 if rec['net_id'] in core:groups[rec['net_id']].add(rec['connection_id'])
for q in event['selection']['queries']:assert q==qm[q['connection_id']];groups[q['net_id']].add(q['connection_id'])
for net,nodeset in original_owners.items():
 if net not in release:
  for n in nodeset:nodeowners[n].add(net)
options={int(n):ops for n,ops in json.loads((out/'core_options.json').read_text()).items()};assert set(options)==set(core);option_nodes={};records_checked=0
for net,ops in options.items():
 for i,op in enumerate(ops):
  assert {x['connection_id'] for x in op['records']}==groups[net] and len(op['records'])==len(groups[net]) and all(x['net_id']==net for x in op['records']);nodeset=own(op['records'])[net];assert sorted(nodeset)==op['nodes'];banned={n for j,n in enumerate(cut) if not op['mask']>>j&1};assert not nodeset.intersection(banned) and not nodeset.intersection(original_owners[88]);option_nodes[net,i]=nodeset;records_checked+=len(op['records'])
selected=json.loads((out/'proposals.json').read_text());assert len(selected)==r['selected_proposals']<=12;scopes=Counter()
for proposal in selected:
 indices={int(n):i for n,i in proposal['core_option_indices'].items()};assert set(indices)==set(core);core_ledger=Counter(n for net,i in indices.items() for n in option_nodes[net,i]);assert all(c<=f['capacities'][n] for n,c in core_ledger.items());extras={net for n,c in core_ledger.items() if c+len(nodeowners[n])>f['capacities'][n] for net in nodeowners[n]};assert 88 not in extras;assert sorted(extras)==proposal['extra_owners'] and not extras.intersection(release);expanded=set(release)|extras;assert sorted(expanded)==proposal['release'];combined=Counter(core_ledger)
 for net,nodeset in original_owners.items():
  if net not in expanded:combined.update(nodeset)
 assert all(c<=f['capacities'][n] for n,c in combined.items());assert proposal['restoration_connection_count']==sum(len(before[n]) for n in expanded)+len(event['selection']['queries']);assert proposal['total_core_physical_edges']==sum(len(x['answer']['physical_edge_ids']) for net,i in indices.items() for x in options[net][i]['records']);scopes[tuple(sorted(expanded))]+=1
assert all(c<=2 for c in scopes.values());assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,complete_core_tree_variants=sum(len(x) for x in options.values()),core_records_verified=records_checked,proposals_verified=len(selected),whole_net_owner_release_and_fixed_seed_plus_core_capacity_pass=True,scope='Physical complete-core paths and remaining kept are safe only after listed owner release; no original released/extra-owner restoration is omitted from required work. This is not an accepted2172candidate, native route, exhaustive minimum release or workflow gain.'),indent=2)+'\n');print('PASS owner proposals',len(selected),records_checked,flush=True)
