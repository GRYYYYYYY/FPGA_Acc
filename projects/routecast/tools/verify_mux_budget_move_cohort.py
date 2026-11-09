"""Independent XML/Fraction budget-ball closure proofs for all fixed moves."""
import json,heapq,xml.etree.ElementTree as ET
from fractions import Fraction
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_budget_move_cohort_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json')and len(r['rows'])==len(p['cases'])==12;assert all(sha(f)==h for f,h in p['sources'].items());rows=[];previous=None
for case,row in zip(p['cases'],r['rows']):
 w=case['width'];i=case['index'];assert w==row['width']and i==row['index'];assert all(sha(f)==h for f,h in case['inputs'].items());file=out/f'w{w}_m{i}/preflight.json';assert sha(file)==row['sha256'];result=json.loads(file.read_text());assert result['status']=='REJECT_BUDGET_CANDIDATE_USE_NATIVE_COLD';last=result['observations'][-1];assert not last['feasible'];ep=json.loads(Path(case['target']).read_text());assert last['query']in ep['connections'];q=last['query'];budget_spec=json.loads(Path(case['budget']).read_text());budget=Fraction(budget_spec['budgets_ns'][str(q['connection_id'])])/10**9
 if w!=previous:
  graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n for n in xml.find('rr_nodes')};caps={n:int(x.get('capacity'))for n,x in nodes.items()};switches={int(s.get('id')):s for s in xml.find('switches')};adj=defaultdict(list)
  for eid,e in enumerate(xml.find('rr_edges')):
   u,v,sw=[int(e.get(k))for k in ('src_node','sink_node','switch_id')];t=nodes[v].find('timing');st=switches[sw].find('timing');assert switches[sw].get('type')in('buffer','mux','tristate');inc=(Fraction(st.get('R','0'))+Fraction(t.get('R'))/2)*Fraction(t.get('C'))+Fraction(st.get('Tdel','0'));assert inc>=0
   if caps[u]>0 and caps[v]>0:adj[u].append((v,eid,inc))
  previous=w
 source,sink=q['source'],q['sink'];t=nodes[source].find('timing');initial=Fraction(t.get('R'))*Fraction(t.get('C'))/2;dist={source:initial}if caps[source]>0 and initial<=budget else {};heap=[(initial,source)]if dist else [];back={}
 while heap:
  d,u=heapq.heappop(heap)
  if dist[u]!=d:continue
  for v,eid,inc in adj[u]:
   nd=d+inc
   if nd<=budget and(v not in dist or nd<dist[v]):dist[v]=nd;back[v]=(u,eid,inc);heapq.heappush(heap,(nd,v))
 assert sink not in dist
 # Realized acyclic predecessor chains plus budget-ball Bellman closure:
 # every reachable edge staying within budget has a finite no-greater label.
 for n,d in dist.items():
  assert d<=budget
  if n!=source:
   prev,eid,inc=back[n];assert dist[prev]+inc==d;seen=set();current=n
   while current!=source:assert current not in seen;seen.add(current);current=back[current][0]
  for v,eid,inc in adj[n]:
   if d+inc<=budget:assert v in dist and dist[v]<=d+inc
 certificate=out/f'w{w}_m{i}/budget_ball_certificate.json';certificate.write_text(json.dumps(dict(query=q,budget_seconds=str(budget),graph_sha256=ep['graph_sha256'],distances={str(n):str(d)for n,d in dist.items()},predecessors={str(n):[u,eid,str(inc)]for n,(u,eid,inc)in back.items()},classification='NO_PATH_WITHIN_EXACT_CONNECTION_BUDGET'),indent=2)+'\n');rows.append(dict(width=w,index=i,query=q,budget_ns=str(budget*10**9),certified_nodes=len(dist),certificate_sha256=sha(certificate)));print(w,i,'certified',len(dist),flush=True)
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='All12 independently originalXML Fraction budget-ball closure and realized acyclic predecessor proofs; exact requestedbudget, relaxedotherNEToccupancy. Not global unrouteability or nativeSTA quality.'),indent=2)+'\n')
