"""Original XML path census on certified delayed-history round0."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
O=R/'experiments/mmc_selective_tree_preflight_v1_2026-10-13';M=R/'experiments/mmc_delayed_history_ablation_v1_2026-10-13/model'
v=json.loads((M/'verification.json').read_text());assert v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];bindings={**v['bindings'],**closure([Path(__file__)]),str(M/'verification.json'):sha(M/'verification.json')};assert all(sha(k)==h for k,h in bindings.items())
p=M/'round0.json';assert sha(p)==bindings[str(p)];state=json.loads(p.read_text());records=state['records'];edges_needed={e for r in records for e in r['answer']['physical_edge_ids']};ep=next(Path(k) for k in bindings if k.endswith('/endpoints.json'));meta=json.loads(ep.read_text());graph=Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256'];cap={};edges={};switches={};stack=[];edge_index=0;types=Counter()
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='switch' and 'id' in el.attrib and 'type' in el.attrib:switches[int(el.get('id'))]=el.get('type');types[el.get('type')]+=1
 if el.tag=='node':cap[int(el.get('id'))]=int(el.get('capacity'));stack[-2].remove(el);el.clear()
 if el.tag=='edge':
  if edge_index in edges_needed:edges[edge_index]=(int(el.get('src_node')),int(el.get('sink_node')),int(el.get('switch_id')))
  edge_index+=1;stack[-2].remove(el);el.clear()
 stack.pop()
assert len(edges)==len(edges_needed) and len(cap)==904438 and edge_index==8097539
ledger={int(k):v for k,v in state['ledger'].items()};groups=defaultdict(list);nonconfig_used=Counter()
for r in records:groups[r['net_id']].append(r)
counts=Counter();rows=[]
for net,rs in sorted(groups.items()):
 clean=0;kept=set();owned=set()
 for r in rs:
  u=r['source'];path={u}
  for eid in r['answer']['physical_edge_ids']:
   src,dst,sw=edges[eid];assert src==u;u=dst;path.add(u)
   if switches[sw] in {'short','buffer'}:nonconfig_used[sw]+=1
  assert u==r['sink'];owned.update(path)
  if all(ledger.get(n,0)<=cap[n] for n in path):clean+=1;kept.update(path)
 eligible=len(rs)>=16;counts['nets']+=1;counts['connections']+=len(rs)
 if eligible:
  counts['threshold_nets']+=1;counts['threshold_connections']+=len(rs);counts['clean_connections']+=clean;counts['clean_union_nodes']+=len(kept);counts['old_union_nodes']+=len(owned);counts['mixed_nets']+=0<clean<len(rs)
 rows.append(dict(net=net,fanout=len(rs),clean_connections=clean,clean_union_nodes=len(kept),old_union_nodes=len(owned)))
assert all(sha(k)==h for k,h in bindings.items());out=O/'estimator_round0_eligibility_v1.json';assert not out.exists();out.write_text(json.dumps(dict(bindings=bindings,counts=dict(counts),switch_type_counts=dict(types),nonconfigurable_used_edge_occurrences=dict(nonconfig_used),pernet=rows,scope='Snapshot path congestion and original XML switch census. No online retained-tree decisions, native equivalence, forced-reroute or measured computational gain proof.'),indent=2)+'\n');print(dict(counts),dict(types),dict(nonconfig_used),flush=True)
