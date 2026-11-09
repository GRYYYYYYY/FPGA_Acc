"""Fixed-budget single-NET avoidance diagnostic; no joint feasibility proof."""
import json,shutil
from pathlib import Path
from collections import defaultdict,Counter
from prepared_csr import read,U64,TYPES
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from csr_integer_sink_bound_search import query
from rc_feasible_cost_region import RCFeasibleCostRegion
from verify_rc_remaining_certificate import verify as certificate
from immutable_xml_prediction_audit import ImmutableXMLAudit
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'multiplier_native_budget_net4_displacement_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');bindings={};reports=[]
def readjson(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
for name in ('mult_6x6',):
 parent=base/'multiplier_rc_repeated_sweeps_2026-10-06'/name;receipt=readjson(parent/'receipt.json');assert all(sha(parent/n)==h for n,h in receipt['outputs_sha256'].items());assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items());pred=readjson(parent/'iteration_4_prediction.json');eps=readjson(parent/'iteration_4_endpoints.json');bs=readjson(base/'multiplier_native_reference_rc_budgets_2026-10-06/budgets.json');budget={r['connection_id']:r['scaled_integer_budget'] for r in bs};m,f=read(base/'multiplier_family_length_switch_csr_2026-10-06'/name/'csr',pred['physical_graph_sha256']);rc=IntegerRC(ExactBufferedRC(f,*load(base/'multiplier_cw300_exact_buffered_rc_classes_2026-10-06'/name,pred['physical_graph_sha256'])));slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])};groups=defaultdict(list)
 for r in pred['connections']:groups[r['net_id']].append(r)
 def union(rows):
  s=set()
  for r in rows:
   s.add(r['source'])
   for eid in r['physical_edge_ids']:s.update(slots[eid])
  return s
 unions={n:union(rows) for n,rows in groups.items()};occ=Counter(n for u in unions.values() for n in u);blocked={n for n,v in occ.items() if v>f['capacities'][n]};blocked.update((259,263,267));owners={n:[net for net,u in unions.items() if n in u] for n in blocked};assert blocked
 protocol=readjson(base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json');graph=protocol['inputs']['graph'];xml=ImmutableXMLAudit(graph['path'],graph['sha256']);bindings[graph['path']]=graph['sha256'];region=RCFeasibleCostRegion(m['nodes'],[(u,f['dest_ranks'][i],rc.increments[i],int(f['costs'][i])) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1]) if u not in blocked and f['dest_ranks'][i] not in blocked and f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0]);cases=[]
 for net in (4,):
  other=occ.copy();other.subtract(unions[net]);candidate=[];connections=[]
  for r in groups[net]:
   source,sink=r['source'],r['sink'];endpoint_blocked=source in blocked or sink in blocked;remaining=region.distance(sink,True);minimum=None if endpoint_blocked or source not in remaining else rc.initial(source)+remaining[source]
   reduced={**f,'costs':[U64 if slots[f['edge_ids'][i]][0] in blocked or f['dest_ranks'][i] in blocked else f['costs'][i] for i in range(m['edges'])]};proof=certificate(reduced,rc.increments,sink,[remaining.get(n,U64) for n in range(m['nodes'])]);assert proof['all_distance_and_tight_path_checks_passed']
   result={'status':'BLOCKED_ENDPOINT'} if endpoint_blocked else query(rc,source,sink,budget[r['connection_id']],lambda u,i:u not in blocked and f['dest_ranks'][i] not in blocked and f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0,lambda u,i:int(f['costs'][i])*(1+other[f['dest_ranks'][i]]),remaining,10000)
   connections.append({'connection_id':r['connection_id'],'minimum_avoidance_rc':minimum,'shortest_rc_certificate':proof,'budget':budget[r['connection_id']],'result':result})
   if result['status']=='FOUND':candidate.append({**r,'method':'avoid_overused','physical_edge_ids':result['physical_edge_ids']})
  report={'net_id':net,'connections':connections,'all_connections_found':len(candidate)==len(groups[net])}
  if report['all_connections_found']:
   rows=[r for r in pred['connections'] if r['net_id']!=net]+candidate;newocc=Counter(n for u in [union([r for r in rows if r['net_id']==n]) for n in groups] for n in u);p={**pred,'connections':sorted(rows,key=lambda r:r['connection_id']),'node_occupancy':{str(n):v for n,v in newocc.items() if v},'methods':dict(Counter(r['method'] for r in rows))};audit=xml.verify(eps,p,topology=True);netreport=next(x for x in audit['net_union_topology']['nets'] if x['net_id']==net);treeok=not netreport['internal_multi_incoming_nodes'] and not netreport['cyclic_union'] and not netreport['source_has_incoming'] and netreport['all_nodes_source_reachable'];report.update({'candidate_overflow':audit['all_type_overuse_units'],'tree_ok':treeok,'strictly_improves':treeok and audit['all_type_overuse_units']<sum(max(0,v-f['capacities'][n]) for n,v in occ.items())})
   (out/f'{name}_net_{net}_candidate.json').write_text(json.dumps(p)+'\n')
  cases.append(report)
 result={'design':name,'blocked_nodes':[{'node':n,'type':next(k for k,v in TYPES.items() if v==f['types'][n]),'capacity':f['capacities'][n],'occupancy':occ[n],'owner_nets':owners[n]} for n in sorted(blocked)],'cases':cases};reports.append(result);print(name,result['blocked_nodes'],[(c['net_id'],c['all_connections_found'],c.get('strictly_improves')) for c in cases],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
(out/'receipt.json').write_text(json.dumps({'inputs_sha256':bindings,'source_sha256':sha(out/'source.py'),'results':reports,'scope':'Independent reduced-graph exact shortest-delay and bounded Pareto search, originally overused IPIN255 and displaced conflict IPIN259 forbidden for one NET at a time. Complete NET candidate/XML union gate if paths exist. No coordinated rerouting infeasibility proof, native legality, transaction publication or timing benefit.'},indent=2)+'\n')
