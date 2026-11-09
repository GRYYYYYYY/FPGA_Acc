"""Independent printed-route expansion, exact Fraction RC and budget occurrence audit."""
import sys,json
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from audit_native_route import NET,NODE
from buffered_rc_node_classes import read,arc_delay
from immutable_xml_prediction_audit import ImmutableXMLAudit
out=R/'experiments/misex_native_reference_proxy_budgets_v1_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());p=json.loads((out/'protocol.json').read_text());assert p['bindings']==r['bindings'];bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(k)==h for k,h in bindings.items());ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);xml=ImmutableXMLAudit(graph,digest);ids,classes,switches,d=read(graph);assert d==digest;route=ep.parent/'design.route';floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json').read_text())};required=Counter((q['net_id'],q['source'],q['sink']) for q in queries);rows=json.loads((out/'reference_rows.json').read_text());assert len(rows)==len(queries)==p['required_connections'];reported=defaultdict(list)
for row in rows:reported[row['net_id'],row['source'],row['sink']].append(row)
assert Counter({k:len(v) for k,v in reported.items()})==required
# Reconstruct the printed parent tree with original XML edge identities.
byarc=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 e=xml.graph.edges[eid];byarc[e.source,e.sink,e.switch_id].append(eid)
seen=Counter();owners=defaultdict(set);net=None;parents={};src=None;previous=None;switch=None;pathmap={}
for line in route.read_text().splitlines():
 m=NET.match(line)
 if m:net=int(m[1]);parents={};pathmap={};src=None;previous=None;switch=None
 m=NODE.match(line)
 if not m:continue
 node=int(m[1]);kind=m[2];next_switch=int(m[3]);assert xml.graph.nodes[node].type==kind;owners[net].add(node)
 if kind=='SOURCE':assert src is None;src=node;pathmap[node]=()
 elif node in pathmap and kind!='SINK':pass
 else:
  assert previous is not None;edges=byarc[previous,node,switch];assert edges;pathmap[node]=pathmap[previous]+(min(edges),)
 if kind=='SINK' and (net,src,node) in required:
  key=(net,src,node);index=seen[key];assert index<required[key];seen[key]+=1;row=reported[key][index];assert row['endpoint_occurrence']==index and row['endpoint_occurrences']==required[key];path=pathmap[node];assert list(path)==row['physical_edge_ids'];initial_r,initial_c=classes[ids[src]];delay=initial_r*initial_c/2;u=src;visited={u}
  for eid in path:
   e=xml.graph.edges[eid];assert e.source==u and e.sink not in visited;u=e.sink;visited.add(u);delay+=arc_delay(classes,switches,ids[u],e.switch_id)
  assert u==node;scaled=delay*rc.scale;assert scaled.denominator==1 and scaled.numerator==row['delay_integer'];floor=floors[src,node];budget=max(rc.scale//10**9,(3*floor+1)//2);assert row['floor_integer']==floor and row['budget_integer']==budget and row['budget_feasible']==(scaled<=budget)
 previous=node;switch=next_switch
assert seen==required;ledger=Counter(n for owned in owners.values() for n in owned);assert all(c<=xml.graph.nodes[n].capacity for n,c in ledger.items());assert dict(ledger)=={int(n):c for n,c in r['physical_reference_audit']['node_occupancy'].items()};assert r['physical_reference_audit']['overflow_units']==0;violations=[x for x in rows if not x['budget_feasible']];s=r['summary'];assert s['required_connections']==s['reference_connections']==len(rows) and s['budget_violations']==len(violations);assert {int(n):c for n,c in s['violating_net_counts'].items()}==dict(Counter(x['net_id'] for x in violations));assert s['scale']==rc.scale and s['max_additive_delay_integer']==max(x['delay_integer'] for x in rows)
for net,count in s['core_budget_counts'].items():
 assert count==dict(total=sum(x['net_id']==int(net) for x in rows),violations=sum(x['net_id']==int(net) and not x['budget_feasible'] for x in rows))
assert all(sha(k)==h for k,h in bindings.items());(out/'verification.json').write_text(json.dumps(dict(bindings=bindings,complete_original_endpoint_occurrences=len(rows),all_printed_reference_paths_fraction_rc_and_union_capacity_pass=True,reference_budget_violations=len(violations),scope='Archived native physical reference only, not predicted candidate, complete proxy-budget solver proof, retuned budget or unseen-family/native workflow-gain evidence.'),indent=2)+'\n');print('PASS reference scalar budgets',len(rows),len(violations),flush=True)
