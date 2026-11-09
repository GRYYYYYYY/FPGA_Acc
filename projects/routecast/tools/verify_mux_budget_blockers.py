"""Verify shortest-distance certificates without rerunning production search."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_budget_blocker_witness_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json') and r['all_cases_retained'];assert p['source_sha256']==sha(root/'tools/diagnose_mux_budget_blockers.py');rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert all(sha(f)==h for f,h in c['bindings'].items());w=c['data_width'];ch=c['channels'];file=out/f'mux_w{w}_w{ch}.json';assert sha(file)==row['certificate_sha256'];certificate=json.loads(file.read_text());prior=json.loads(Path(c['receipt']).read_text());ep=json.loads(Path(c['endpoints']).read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==certificate['graph_sha256']==ep['graph_sha256'];xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};edges=[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))) for e in xml.find('rr_edges')];switches={int(s.get('id')):s for s in xml.find('switches')};query=prior['failure']['query'];assert query==certificate['query'];own=set()
 for rec in prior['records']:
  if rec['net_id']==query['net_id']:
   own.add(rec['source'])
   for eid in rec['answer']['physical_edge_ids']:own.add(edges[eid][1])
 ledger={int(n):v for n,v in prior['ledger'].items()};allowed={n for n,node in nodes.items() if int(node.get('capacity'))>0};assert sorted(allowed)==certificate['allowed_nodes'];dist={int(n):Fraction(v) for n,v in certificate['distances'].items()};back={int(n):tuple(v) for n,v in certificate['predecessors'].items()};source=query['source'];sink=query['sink'];timing=nodes[source].find('timing');initial=Fraction(timing.get('R'))*Fraction(timing.get('C'))/2
 def inc(eid):
  u,v,s=edges[eid];t=nodes[v].find('timing');st=switches[s].find('timing');assert switches[s].get('type') in ('buffer','mux','tristate');return (Fraction(st.get('R','0'))+Fraction(t.get('R'))/2)*Fraction(t.get('C'))+Fraction(st.get('Tdel','0'))
 assert set(dist)<=allowed and set(back)==set(dist)-{source}
 if source in allowed:assert dist[source]==initial
 else:assert not dist
 # Realized finite labels; walking every predecessor chain rules out zero-cost cycles.
 for n in back:
  seen=set();current=n
  while current!=source:
   assert current not in seen;seen.add(current);prev,eid=back[current];assert edges[eid][:2]==(prev,current) and dist[prev]+inc(eid)==dist[current];current=prev
 # Bellman inequalities on every original admissible edge certify lower bound and closure.
 for eid,(u,v,s) in enumerate(edges):
  if u in dist and v in allowed:assert v in dist and inc(eid)>=0 and dist[v]<=dist[u]+inc(eid)
 classification='CAPACITY_DISCONNECTED' if sink not in dist else 'MIN_DELAY_OVER_1NS' if dist[sink]>Fraction(1,10**9) else 'WITHIN_BUDGET_GRAPH_PATH_EXISTS';assert classification==row['classification'];path=certificate['physical_edge_ids'];node=source;value=initial
 for eid in path:assert edges[eid][0]==node;node=edges[eid][1];value+=inc(eid)
 if sink in dist:assert node==sink and value==dist[sink] and float(value*10**9)==row['minimum_delay_ns']
 else:assert not path and row['minimum_delay_ns'] is None
 unions={}
 for rec in prior['records']:
  used=unions.setdefault(rec['net_id'],set());used.add(rec['source'])
  for eid in rec['answer']['physical_edge_ids']:used.add(edges[eid][1])
 witness_nodes={source}|{edges[eid][1] for eid in path};blocked=sorted(n for n in witness_nodes if ledger.get(n,0)-int(n in own)>=int(nodes[n].get('capacity')))
 assert blocked==certificate['blocked_nodes']
 owners={str(n):sorted(net for net,used in unions.items() if net!=query['net_id'] and n in used) for n in blocked};assert owners==certificate['owners']
 release=sorted({net for v in owners.values() for net in v});assert release==certificate['release_NETs']==row['release_NETs']
 for n in witness_nodes:
  residual=ledger.get(n,0)-int(n in own)-sum(n in unions[net] for net in release)
  assert 0<=residual<int(nodes[n].get('capacity'))
 assert sink in dist and dist[sink]<=Fraction(1,10**9)
 rows.append({'data_width':w,'channels':ch,'classification':classification,'minimum_delay_ns':row['minimum_delay_ns'],'all_distance_labels_certified':len(dist)});print(w,ch,classification,flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'Fresh originalXML exactFraction RC and ledgermask reconstruction, realized acyclic predecessor chains and all-edge Bellman inequalities; graph-only minimum ignores tree constraints, does not prove native STA or global unrouteability.'},indent=2)+'\n')
