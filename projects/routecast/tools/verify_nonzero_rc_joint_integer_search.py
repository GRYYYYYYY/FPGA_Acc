"""Original XML witness, exact delay, per-query capacity and lattice audit."""
import json,csv
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_joint_integer_search_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_nonzero_rc_joint_integer_search.py')==r['source_sha256'];assert sha(root/'build/rc_capacity_native_2026-10-06/search.so')==r['library_sha256'];work=root/'work/nonzero_rc_fanout_observable64_2026-10-06';graph=work/'rr_graph.xml';audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);table=work/'before_sync.delays.tsv';assert sha(table)==r['native_table_sha256'];rows=list(csv.DictReader(table.open(),delimiter='\t'));unions=defaultdict(set);required={}
for row in rows:
 net=int(row['net']);unions[net].add(int(row['node']))
 if int(row['pin'])>0:required[(net,int(row['pin']))]=int(row['node'])
unions=defaultdict(set);ledger=Counter();checked=0;nonzero_paths=0;arcs=defaultdict(set);failure=None
for q in r['results']:
 assert required.pop((q['net_id'],q['pin_index']))==q['sink'];answer=q['result'];
 if answer['status']!='FOUND':assert q is r['results'][-1];failure=answer['status'];break
 node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);arcs[q['net_id']].add((e.source,e.sink,eid));delay+=arc_delay(classes,switches,ids[node],e.switch_id)
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['transport']['scale']) and delay<=Fraction(1,10**9);assert answer['delay']<=r['budget_integer'];assert answer['cost']==sum((ledger[n]-int(n in unions[q['net_id']])+1) for n in list(used-{q['source']}))
 for n in used:assert ledger[n]-int(n in unions[q['net_id']])<audit.caps[n]
 ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used)
 nonzero_paths+=int(any(classes[ids[n]][0]>0 and classes[ids[n]][1]>0 for n in used));checked+=1
assert checked==57 and failure=='UNREACHABLE' and nonzero_paths>0 and len(r['results'])==58 and r['required_connections']==69;assert not r['overflow_nodes'];assert all(v<=audit.caps[n] for n,v in ledger.items());parents=defaultdict(set)
for net,edges in arcs.items():
 for u,v,eid in edges:parents[(net,v)].add((u,eid))
bad=[{'net':net,'node':n,'parents':len(p)} for (net,n),p in parents.items() if len(p)>1];assert bad==r['multi_parent_nodes']
(out/'verification.json').write_text(json.dumps({'connections':checked,'required_connections':69,'failure':failure,'multi_parent_nodes':bad,'overflow_units':0,'nonzero_RC_paths':nonzero_paths,'scale_bits':r['transport']['scale_bits'],'maximum_arc_increment_bits':r['transport']['max_increment_bits'],'graph_sha256':audit.digest,'receipt_sha256':sha(out/'receipt.json'),'scope':'All original XML arcs/simple paths/endpoints, exact rational delay equals native integer witness under fixed1ns budget, original per-query capacity after own NET release, exact unit-edge other-demand cost. Sequential joint greedy successful prefix:57/69 complete, next query UNREACHABLE under1ns fixed budget. No overflow in partial union ledger, native residual/local OPIN demand unverified. Failure is not a native/global infeasibility proof; incomplete seed cannot be published.'},indent=2)+'\n');print('verified',checked,'exact integer witnesses;',nonzero_paths,'nonzero-RC paths')
