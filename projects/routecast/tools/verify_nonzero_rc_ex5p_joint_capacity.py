"""Independent sequential originalXML demand/parent/fallback-budget event audit."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/nonzero_rc_ex5p_joint_capacity_2026-10-06';r=json.loads((out/'receipt.json').read_text());protocol=json.loads((out/'protocol.json').read_text());ep=root/'experiments/nonzero_rc_ex5p_endpoints_2026-10-06/endpoints.json';endpoints=json.loads(ep.read_text());assert protocol['endpoint_sha256']==sha(ep) and r['protocol_sha256']==sha(out/'protocol.json') and r['source_sha256']==sha(root/'tools/trial_nonzero_rc_ex5p_joint_capacity.py');assert all(sha(v['path'])==v['sha256'] for v in endpoints['inputs'].values());graph=Path(endpoints['inputs']['graph']['path']);audit=ImmutableXMLAudit(graph,r['graph_sha256']);ids,classes,switches,_=read(graph);queries=sorted(endpoints['connections'],key=lambda q:(q['net_id'],q['connection_id']));ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict);fallbacks=0;checked=0
assert r['required_connections']==len(queries)==1916 and len(r['attempts'])==len(r['records'])+1
for index,attempt in enumerate(r['attempts']):
 q=queries[index];assert q==attempt['query'];net=q['net_id'];other=Counter(ledger)
 for n in unions[net]:other[n]-=1
 native=attempt['native_answer'];answer=native;mode='NATIVE_UNIT_COST'
 if 'fallback_answer' in attempt:
  assert native['status'] in ('LABEL_LIMIT','UNREACHABLE') and fallbacks<64;fallbacks+=1;answer=attempt['fallback_answer'];mode='MINIMUM_DELAY_FALLBACK'
 if index==len(r['records']):
  assert answer['status']=='LABEL_LIMIT' and fallbacks==64 and 'fallback_answer' not in attempt and r['failure']=={'query':q,'status':'LABEL_LIMIT'};break
 record=r['records'][index];assert all(record[k]==value for k,value in q.items()) and record['mode']==mode and record['answer']==answer and answer['status']=='FOUND';node=q['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;incoming={};assert other[node]<audit.caps[node]
 for eid in answer['physical_edge_ids']:
  e=audit.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);assert other[node]<audit.caps[node];delay+=arc_delay(classes,switches,ids[node],e.switch_id);cost+=1+other[node];incoming[node]=(e.source,eid)
 assert node==q['sink'] and delay==Fraction(answer['delay'],r['scale'])<=Fraction(1,10**9)
 if mode=='NATIVE_UNIT_COST':assert answer['cost']==cost
 assert all(n not in parents[net] or parents[net][n]==p for n,p in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);checked+=1
assert dict(ledger)=={int(n):v for n,v in r['ledger'].items()} and checked==r['completed_connections']==170 and fallbacks==r['fallbacks']==64 and r['status']=='INCOMPLETE_NOT_PUBLISHABLE';assert all(v<=audit.caps[n] for n,v in ledger.items());(out/'verification.json').write_text(json.dumps({'accepted_paths_checked':checked,'fallback_witnesses_checked':fallbacks,'prefix_capacity_overflow_units':0,'prefix_multi_parent_nodes':0,'failed_query_not_committed':True,'frozen_fallback_ceiling_respected':True,'receipt_sha256':sha(out/'receipt.json'),'scope':'OriginalXML paths/exact1ns/native unitcost and sequential NETunion capacity/parents audited, including successful fallback witnesses. Fallback optimum not independently certified here; final LABEL_LIMIT not infeasibility. Incomplete170/1916 prefix not published/nativeFULL/STA/benefit.'},indent=2)+'\n');print('verified170 retained joint paths, zero overflow/parents,64 fallback witnesses; final query not committed')
