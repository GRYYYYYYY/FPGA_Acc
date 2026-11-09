"""Exact integer hard-capacity search on full original nonzero-RC graph."""
import json,csv,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from array import array
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from native_capacity_rc_search import NativeCapacityRC
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_joint_integer_search_2026-10-06';out.mkdir();parent=root/'experiments/nonzero_rc_fanout_observable64_2026-10-06';receipt=json.loads((parent/'receipt.json').read_text());proof=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'];assert all(sha(p)==h for p,h in receipt['files_sha256'].items());work=root/'work/nonzero_rc_fanout_observable64_2026-10-06';graph=work/'rr_graph.xml';digest=sha(graph);xml=ET.parse(graph).getroot();nodes=list(xml.find('rr_nodes'));adj=defaultdict(list)
for eid,e in enumerate(xml.find('rr_edges')):adj[int(e.get('src_node'))].append((int(e.get('sink_node')),int(e.get('switch_id')),eid))
f={name:array('Q') for name in ('node_ids','row_offsets','dest_ranks','edge_ids','switch_ids','costs','capacities')};f['node_ids'].extend(range(len(nodes)));f['capacities'].extend(int(n.get('capacity')) for n in nodes);f['row_offsets'].append(0)
for u in range(len(nodes)):
 for v,s,eid in adj[u]:f['dest_ranks'].append(v);f['switch_ids'].append(s);f['edge_ids'].append(eid);f['costs'].append(1)
 f['row_offsets'].append(len(f['edge_ids']))
rc=IntegerRC(ExactBufferedRC(f,*read(graph)[:3]));transport={'scale':rc.scale,'scale_bits':rc.scale.bit_length(),'max_increment':max(rc.increments),'max_increment_bits':max(rc.increments).bit_length(),'nodes':len(nodes),'edges':len(f['edge_ids'])};(out/'transport.json').write_text(json.dumps(transport,indent=2)+'\n');native=NativeCapacityRC(rc);budget=(Fraction(1,10**9)*rc.scale).__floor__();rows=list(csv.DictReader((work/'before_sync.delays.tsv').open(),delimiter='\t'));unions=defaultdict(set);roots={};queries=[]
for r in rows:
 net=int(r['net']);node=int(r['node']);unions[net].add(node)
 if nodes[node].get('type')=='SOURCE':assert net not in roots;roots[net]=node
 if int(r['pin'])>0:queries.append({'net_id':net,'pin_index':int(r['pin']),'sink':node,'native_delay_s':r['delay_s']})
original_unions=unions;ledger=Counter();unions=defaultdict(set);results=[];arcs=defaultdict(set);slots={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(len(nodes)) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
for q in sorted(queries,key=lambda x:(x['net_id'],x['pin_index'])):
 other=Counter(ledger)
 for node in unions[q['net_id']]:other[node]-=1
 native.set_other(dict(+other));answer=native.query(roots[q['net_id']],q['sink'],budget,max_labels=10000);results.append({**q,'source':roots[q['net_id']],'result':answer})
 if answer['status']!='FOUND':break
 used={roots[q['net_id']]};node=roots[q['net_id']]
 for eid in answer['physical_edge_ids']:
  u,v=slots[eid];assert u==node;node=v;used.add(node);arcs[q['net_id']].add((u,v,eid))
 ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used)
parents=defaultdict(set)
for net,edges in arcs.items():
 for u,v,eid in edges:parents[(net,v)].add((u,eid))
bad=[{'net':net,'node':n,'parents':len(p)} for (net,n),p in parents.items() if len(p)>1];overflow={n:v-f['capacities'][n] for n,v in ledger.items() if v>f['capacities'][n]}

(out/'receipt.json').write_text(json.dumps({'results':results,'multi_parent_nodes':bad,'overflow_nodes':overflow,'required_connections':len(queries),'transport':transport,'budget_integer':budget,'max_labels':10000,'graph_sha256':digest,'native_table_sha256':sha(work/'before_sync.delays.tsv'),'parent_verification_sha256':sha(parent/'verification.json'),'source_sha256':sha(Path(__file__)),'library_sha256':sha(root/'build/rc_capacity_native_2026-10-06/search.so'),'scope':'All full original RR arcs, unit edge-cost objective, fixed1ns branch allowance, hard other-NET capacity, all routable NET unions released first, sequential NET/pin order with own predicted union excluded and unique NET/node ledger. Complete cohort attempted, no native seed publication or residual OPIN certification; exact lattice without quantization.'},indent=2)+'\n');print(transport,Counter(x['result']['status'] for x in results))
