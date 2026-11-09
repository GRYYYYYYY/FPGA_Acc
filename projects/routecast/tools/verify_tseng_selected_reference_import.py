"""Independent XML reconstruction of selected native ledger and next candidate."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_selected_reference_import_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text())
assert r['protocol_sha256']==sha(out/'protocol.json') and r['incumbent_sha256']==sha(out/'incumbent.json') and r['update_sha256']==sha(out/'update.json')
assert all(sha(f)==h for f,h in p['inputs_sha256'].items()) and all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items())
ep=json.loads((root/'experiments/tseng_placement_swap_2026-10-06/endpoints.json').read_text());target=json.loads((root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json').read_text());selected=root/'work/tseng_swapped_quality_gate_2026-10-06/design.route';graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)
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
inc=json.loads((out/'incumbent.json').read_text());expected,ledger=check(inc,ep)
native=audit(graph,selected);assert native['overflow_units']==0 and {int(n):c for n,c in native['node_occupancy'].items()}==dict(ledger)
# Independent native parser is copied from prior canonical verifier, not importer.
import re
from audit_native_route import NODE
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
native_paths=physical_by_name(selected)
excluded={x['net'] for x in ep['excluded_nets']}
assert all(not native_paths.get(name,[]) for name in excluded)
assert expected=={name:rows for name,rows in native_paths.items() if name not in excluded}
update=json.loads((out/'update.json').read_text());final=update['repair'] or update['incremental'];check(final,target)
assert update['status']=='COMPLETE_CANDIDATE' and update['repair'] is None and r['live_state_restored']
changed={q['connection_id'] for q,old in zip(target['connections'],ep['connections']) if q!=old};affected={q['net_id'] for q in target['connections'] if q['connection_id'] in changed}
assert set(final['affected']['affected_net_ids'])==affected
prior={q['connection_id']:q for q in inc['records']}
assert all(rec==prior[rec['connection_id']] for rec in final['records'] if rec['net_id'] not in affected)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'selected_native_paths_exact':True,'selected_reference_connections':1234,'next_candidate_connections':1234,'overflow_units':0,'multi_parent_nodes':0,'unaffected_records_preserved':True,'scope':'Original XML physical/endpoints/exact RC/perNET unioncapacity/parent audit of imported selected reference and next complete candidate. Native selected paths exact; next candidate FULL/STA and event-cost/minimality not verified here. No publication/concurrent commit or speed-benefit claim.'},indent=2)+'\n')
print('verified1234 actual selected reference paths and1234 reverse-update candidate paths')
