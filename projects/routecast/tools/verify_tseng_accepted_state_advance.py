"""Independently audit actual accepted-state advancement snapshots."""
import json,re
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NODE
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_accepted_state_advance_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(path)==h for path,h in p['inputs_sha256'].items()) and all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items())
assert r['final_revision']==2 and len(r['states'])==2
def check(snapshot,endpoints):
 queries={q['connection_id']:q for q in endpoints['connections']};ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict);physical=defaultdict(list)
 assert len(snapshot['records'])==len(queries)==1234 and {q['connection_id'] for q in snapshot['records']}==set(queries)
 for record in snapshot['records']:
  q=queries[record['connection_id']];assert all(record[k]==v for k,v in q.items());node=q['source'];used={node};path=[(node,None)];res,cap=classes[ids[node]];delay=res*cap/2;net=q['net_id']
  for eid in record['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id);path.append((node,e.switch_id));parent=(e.source,eid)
   assert node not in parents[net] or parents[net][node]==parent;parents[net][node]=parent
  assert node==q['sink'] and delay==Fraction(record['answer']['delay'],snapshot['scale'])
  ledger.update(used-unions[net]);unions[net].update(used);physical[endpoints['net_names'][str(net)]].append(tuple(path))
 assert dict(ledger)=={int(n):c for n,c in snapshot['ledger'].items()} and all(c<=xml.caps[n] for n,c in ledger.items())
 return {name:sorted(rows) for name,rows in physical.items()},ledger
def physical_by_name(path):
 nets={};name=None;parents={};previous=None;switch=None
 for line in path.read_text().splitlines():
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
  if m:name=m[1];assert name not in nets;nets[name]=[];parents={};previous=None;continue
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':nets[name].append(tuple(parents[previous]+[(node,switch)]))
  elif node not in parents:parents[node]=parents[previous]+[(node,switch)]
  previous=node;switch=int(m[3])
 return {name:sorted(paths) for name,paths in nets.items()}
checked=[]
for i,row in enumerate(r['states']):
 ep=json.loads(Path(row['endpoint_path']).read_text());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)
 path=out/f'state{i}.json';assert sha(path)==row['state_sha256'];snapshot=json.loads(path.read_text());paths,ledger=check(snapshot,ep)
 gate=Path(row['gate']);selection=json.loads((gate/'selection.json').read_text());v=json.loads((gate/'verification.json').read_text());assert selection['selected']=='reference' and v['selection_sha256']==sha(gate/'selection.json') and v['FULL_reload_success']
 routes=[Path(f) for f in selection['files_sha256'] if Path(f).name=='design.route'];assert len(routes)==1;route=routes[0];assert sha(route)==selection['files_sha256'][str(route)]
 native=physical_by_name(route);excluded={x['net'] for x in ep['excluded_nets']};assert all(not native.get(n,[]) for n in excluded);assert paths=={n:rows for n,rows in native.items() if n not in excluded}
 physical=audit(graph,route);assert physical['overflow_units']==0 and {int(n):c for n,c in physical['node_occupancy'].items()}==dict(ledger)
 assert row['revision']==i+1;checked.append({'revision':i+1,'connections':1234,'selected_reference_paths_exact':True,'overflow_units':0,'multi_parent_nodes':0})
assert set(r['checks'])=={'wrong-placement-selection','mutated-prepared-ledger','stale-history-token','reset-exception-restores-history-demand-state','consumed-preparation-0','consumed-preparation-1'}
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'states':checked,'contract_checks':r['checks'],'scope':'Actual two accepted-reference ledger snapshots independently originalXML/endpoints/RC/unioncapacity/parent and selected physical path audited. Rejection/exception checks asserted by authenticated trial; no concurrent readers, process-crash recovery or full update costs covered.'},indent=2)+'\n');print('verified two accepted revisions,2468 paths and6 rejection/rollback contracts')
