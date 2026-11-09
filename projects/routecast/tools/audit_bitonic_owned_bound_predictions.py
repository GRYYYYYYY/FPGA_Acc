"""Independent original-XML prefix RC, dynamic owner-cost and ledger replay."""
import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_owned_bound_prediction_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());assert all(sha(f)==h for f,h in p['inputs'].items());rows=[]
for row in r['rows']:
 n=row['count'];file=out/f'n{n}.json';assert sha(file)==row['candidate_sha256'];c=json.loads(file.read_text());epfile=next(Path(f) for f in p['inputs'] if Path(f).parent.name==f'n{n}');ep=json.loads(epfile.read_text());assert set(ep['inputs'])=={'net','place','graph'} and all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());graph=Path(ep['inputs']['graph']['path']);a=ImmutableXMLAudit(graph,c['graph_sha256']);ids,classes,switches,_=read(graph);queries=sorted(ep['connections'],key=lambda q:(q['net_id'],q['connection_id']));ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict);checked=0
 assert c['required_connections']==len(queries) and len(c['attempts']) in (len(c['records']),len(c['records'])+1) and c['fallbacks']==0
 for k,event in enumerate(c['attempts']):
  q=queries[k];assert q==event['query'];net=q['net_id'];assert event['wire_owner_union']==sorted(unions[net]);answer=event['native_answer'];other={node:count-int(node in unions[net]) for node,count in ledger.items()}
  if k==len(c['records']):assert answer['status']!='FOUND' and c['failure']==dict(query=q,status=answer['status']);break
  record=c['records'][k];assert all(record[key]==v for key,v in q.items()) and record['answer']==answer and answer['status']=='FOUND';node=q['source'];used={node};incoming={};res,cap=classes[ids[node]];delay=res*cap/2;cost=F(0);assert other.get(node,0)<a.caps[node]
  for eid in answer['physical_edge_ids']:
   edge=a.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);assert other.get(node,0)<a.caps[node];inc=arc_delay(classes,switches,ids[node],edge.switch_id);delay+=inc;penalty=F(1,20*10**9)*a.spans[node] if a.types[node] in (4,5) and node not in unions[net] else F(0);cost+=(inc+penalty)*c['scale']*(1+other.get(node,0));incoming[node]=(edge.source,eid)
  assert node==q['sink'] and delay==F(answer['delay'],c['scale'])<=F(1,10**9);assert cost==answer['cost'];assert all(node not in parents[net] or parents[net][node]==parent for node,parent in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);checked+=1
 assert dict(ledger)=={int(k):v for k,v in c['ledger'].items()} and checked==len(c['records'])==c['completed_connections'];assert all(count<=a.caps[node] for node,count in ledger.items());assert (c['failure'] is None)==(checked==len(queries));rows.append(dict(count=n,status=c['status'],accepted_paths_checked=checked,required_connections=len(queries),prefix_overflow_units=0,prefix_parent_conflicts=0,candidate_sha256=sha(file)));print(n,checked,'candidate paths/delay/owner-cost audited',flush=True)
assert all(sha(f)==h for f,h in p['sources'].items());(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),auditor_sha256=sha(Path(__file__)),rows=rows,scope='All3 retained, each committed prefix original XML edges/switches/SOURCE/SINK/exactbufferedRC<=1ns/owner-wire dynamiccost/uniqueNET capacity/parents independently replayed. Incomplete label-limit witness retained, no failure minimality proof. Not nativecandidateFULLSTA/QoR, strictheldout or netgain.'),indent=2)+'\n')
