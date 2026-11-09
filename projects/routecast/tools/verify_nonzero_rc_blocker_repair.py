import json
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from nonzero_rc_search_context import load
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_blocker_repair_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert sha(root/'tools/trial_nonzero_rc_blocker_repair.py')==r['source_sha256'];graph,digest,nodes,f,rc,queries,_=load(root);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);required={(q['net_id'],q['pin_index']):(q['source'],q['sink']) for q in queries};parent=root/'experiments/nonzero_rc_joint_integer_search_2026-10-06';proof=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==proof['receipt_sha256'] and sha(parent/'verification.json')==r['parent_verification_sha256'];old=json.loads((parent/'receipt.json').read_text());retained={(q['net_id'],q['pin_index']):q for q in old['results'][:-1] if q['net_id'] not in r['blocker_nets']};ledger=Counter();unions=defaultdict(set);arcs=defaultdict(set);seen=set()
for q in r['records']:
 key=(q['net_id'],q['pin_index']);assert key not in seen;seen.add(key);assert required[key]==(q['source'],q['sink']);answer=q['result'];assert answer['status']=='FOUND'
 if q['origin']=='RETAINED':assert answer==retained.pop(key)['result']
 else:
  expected=Counter(ledger)
  for n in unions[q['net_id']]:expected[n]-=1
  assert dict(+expected)=={int(n):v for n,v in q['other_before'].items()}
 node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);arcs[(q['net_id'],node)].add((e.source,eid));delay+=arc_delay(classes,switches,ids[node],e.switch_id)
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9)
 if q['origin']=='REPAIRED':
  other={int(n):v for n,v in q['other_before'].items()};assert all(other.get(n,0)<audit.caps[n] for n in used);assert answer['cost']==sum(other.get(n,0)+1 for n in used-{q['source']})
 ledger.update(used-unions[q['net_id']]);unions[q['net_id']].update(used)
assert not retained and len(seen)==r['completed_connections']==63 and r['required_connections']==69;assert all(v<=audit.caps[n] for n,v in ledger.items()) and all(len(p)==1 for p in arcs.values());assert not r['overflow_nodes'] and not r['multi_parent_nodes'];assert r['failure']['result']['status']=='UNREACHABLE';assert (53,1) in seen
(out/'verification.json').write_text(json.dumps({'completed_connections':63,'required_connections':69,'original_failed_query_repaired':True,'blocker_nets':r['blocker_nets'],'new_failed_query':{k:r['failure'][k] for k in ('net_id','pin_index','source','sink')},'overflow_units':0,'multi_parent_nodes':0,'receipt_sha256':sha(out/'receipt.json'),'scope':'Original XML all63 retained/repaired paths and exact1ns delays, original record provenance, each repair occupancy/cost context and final per-NET capacity/tree-parent replay. First failed connection recovered, later failure remains; incomplete candidate not publishable. No native residual/nonconfigurable/FULL/STA proof or global infeasibility claim.'},indent=2)+'\n');print('verified63/69; repaired NET53 pin1; new failure NET',r['failure']['net_id'])
