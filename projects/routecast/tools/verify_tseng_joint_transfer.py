"""Independent sequential originalXML demand/parent/fallback-budget event audit."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_joint_transfer_2026-10-06';r=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());ep=root/'experiments/nonzero_rc_tseng_endpoints_2026-10-06/endpoints.json';endpoints=json.loads(ep.read_text());assert protocol['endpoint_sha256']==sha(ep) and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_tseng_joint_transfer.py');assert all(sha(v['path'])==v['sha256'] for v in endpoints['inputs'].values());graph=Path(endpoints['inputs']['graph']['path']);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);queries=sorted(endpoints['connections'],key=lambda q:(q['net_id'],q['connection_id']));ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict);fallbacks=0;checked=0
assert r['required_connections']==len(queries) and len(r['attempts']) in (len(r['records']),len(r['records'])+1)
for index,attempt in enumerate(r['attempts']):
 q=queries[index];assert q==attempt['query'];net=q['net_id'];other=Counter(ledger)
 for n in unions[net]:other[n]-=1
 native=attempt['native_answer'];answer=native;mode='NATIVE_DELAY_COST'
 if 'fallback_answer' in attempt:
  assert native['status'] in ('LABEL_LIMIT','UNREACHABLE') and fallbacks<64;fallbacks+=1;answer=attempt['fallback_answer'];mode='MINIMUM_DELAY_FALLBACK'
 if index==len(r['records']):
  assert answer['status']!='FOUND' and r['failure']=={'query':q,'status':answer['status']};failed_other=dict(+other);failed_query=q;break
 record=r['records'][index];assert all(record[k]==value for k,value in q.items()) and record['mode']==mode and record['answer']==answer and answer['status']=='FOUND';node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;incoming={};assert other[node]<audit.caps[node]
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);assert other[node]<audit.caps[node];increment=arc_delay(classes,switches,ids[node],e.switch_id);delay+=increment;cost+=increment*r['scale']*(1+other[node]);incoming[node]=(e.source,eid)
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9)
 if mode=='NATIVE_DELAY_COST':assert answer['cost']==cost
 assert all(n not in parents[net] or parents[net][n]==p for n,p in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);checked+=1
assert dict(ledger)=={int(n):v for n,v in r['ledger'].items()}
assert checked==r['completed_connections']==len(r['records']) and fallbacks==r['fallbacks']<=64
assert all(v<=audit.caps[n] for n,v in ledger.items())
assert (r['failure'] is None)==(checked==len(queries))
assert all(sha(root/'tools'/name)==digest for name,digest in protocol['sources'].items())
(out/'verification.json').write_text(json.dumps({'accepted_paths_checked':checked,'required_connections':len(queries),'fallback_attempts_checked':fallbacks,'prefix_capacity_overflow_units':0,'prefix_multi_parent_nodes':0,'receipt_sha256':sha(out/'receipt.json'),'scope':'Original XML sequential path/RC/cost/unioncapacity/parent prefix audit. No independent failure minimality proof, native candidate acceptance or family holdout claim.'},indent=2)+'\n')
print('verified',checked,'prefix paths, zerooverflow and parent conflicts')
