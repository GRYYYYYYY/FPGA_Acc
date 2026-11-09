"""Independent sequential originalXML exactRC/cost/NETunion and failed residual audit."""
import json
from pathlib import Path
from collections import Counter,defaultdict,deque
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_RC_preserving_NET_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and r['all_cases_retained'] and len(r['rows'])==9;assert all(sha(root/'tools'/n)==h for n,h in p['sources_sha256'].items());native=root/'experiments/mux_crossbar_channel_pressure_2026-10-06';nv=json.loads((native/'verification.json').read_text());nr=json.loads((native/'receipt.json').read_text());assert nv['receipt_sha256']==sha(native/'receipt.json');labels={(x['data_width'],x['channels']):x['classification'] for x in nv['rows']};rows=[]
for row in r['rows']:
 row={**row,'mode':'soft'}
 w=row['data_width'];ch=row['channels'];case=next(c for c in p['cases'] if c['data_width']==w and c['channels']==ch);assert sha(case['endpoint_path'])==case['endpoint_sha256'];ep=json.loads(Path(case['endpoint_path']).read_text());file=out/f"mux_w{w}_c{ch}.json";assert sha(file)==row['candidate_sha256'];q=json.loads(file.read_text());xml=ImmutableXMLAudit(ep['inputs']['graph']['path'],ep['graph_sha256']);ids,classes,switches,_=read(ep['inputs']['graph']['path']);queries=sorted(ep['connections'],key=lambda x:(x['net_id'],x['connection_id']));unions=defaultdict(set);parents=defaultdict(dict);ledger=Counter();soft=row['mode']=='soft';assert q['soft_capacity']==soft;overbudget=0
 for expected,rec in zip(queries,q['records']):
  assert all(rec[k]==v for k,v in expected.items());net=rec['net_id'];other={n:v-int(n in unions[net]) for n,v in ledger.items()};node=rec['source'];used={node};res,cap=classes[ids[node]];delay=res*cap/2;cost=0;incoming={};assert xml.caps[node]>0 and (soft or other.get(node,0)<xml.caps[node])
  for eid in rec['answer']['physical_edge_ids']:
   edge=xml.graph.edges[eid];assert edge.source==node and edge.sink not in used;node=edge.sink;used.add(node);assert xml.caps[node]>0 and (soft or other.get(node,0)<xml.caps[node]);increment=arc_delay(classes,switches,ids[node],edge.switch_id);delay+=increment;cost+=increment*q['scale']*(1+(0 if node in unions[net] else other.get(node,0)));incoming[node]=(edge.source,eid)
  assert node==rec['sink'] and delay==Fraction(rec['answer']['delay'],q['scale']) and cost==rec['answer']['cost'];assert all(n not in parents[net] or parents[net][n]==v for n,v in incoming.items());parents[net].update(incoming);ledger.update(used-unions[net]);unions[net].update(used);overbudget+=delay>Fraction(1,10**9)
 assert len(q['records'])==q['completed_connections'];assert dict(ledger)=={int(n):v for n,v in q['ledger'].items()};overflow=sum(max(0,v-xml.caps[n]) for n,v in ledger.items());assert overflow==q['overflow_units']==row['overflow_units'] and overbudget==q['over_1ns_connections'];assert len(queries)==q['required_connections'];assert len(q['events'])==len(q['records'])+int(q['failure'] is not None)
 for i,event in enumerate(q['events']):assert event['query']==queries[i] and event['committed']==(i<len(q['records']))
 if q['failure'] is not None:
  failed=queries[len(q['records'])];assert q['failure']['query']==failed;net=failed['net_id'];other={n:v-int(n in unions[net]) for n,v in ledger.items()};adj=defaultdict(list)
  for eid in range(len(xml.graph.edges)):
   e=xml.graph.edges[eid]
   if xml.caps[e.sink]>0 and (soft or other.get(e.sink,0)<xml.caps[e.sink]) and e.sink!=failed['source'] and (e.sink not in parents[net] or parents[net][e.sink]==(e.source,eid)):adj[e.source].append(e.sink)
  seen={failed['source']} if xml.caps[failed['source']]>0 and (soft or other.get(failed['source'],0)<xml.caps[failed['source']]) else set();queue=deque(seen)
  while queue:
   for n in adj[queue.popleft()]:
    if n not in seen:seen.add(n);queue.append(n)
  assert failed['sink'] not in seen
 else:assert q['completed_connections']==q['required_connections']
 rows.append({'data_width':w,'channels':ch,'mode':row['mode'],'connections_checked':len(q['records']),'overflow_units':overflow,'complete_forecast':q['failure'] is None,'native_classification':labels[w,ch]});print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'All9 RC-preserving-NET policy outcomes independently originalXML endpoint/path/exactRC/sequentialRCpreservingNETcost/treeparent/NETunion/eventorder/overflow and residual failure reachability verified. No all-query shortest-cost proof or native legality/forecastaccuracy claim; soft overuse is not routability proof.'},indent=2)+'\n')
