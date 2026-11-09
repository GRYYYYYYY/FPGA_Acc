"""Independent rawXML shortest-distance certificate and terminal capacity cut."""
import json,shutil,heapq
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from collections import defaultdict,deque
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'multiplier_terminal_cut_xml_certificate_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');bindings={}
def readjson(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
name='mult_6x6';parent=base/'multiplier_rc_repeated_sweeps_2026-10-06'/name;receipt=readjson(parent/'receipt.json');assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items());assert all(sha(parent/n)==h for n,h in receipt['outputs_sha256'].items());ep=readjson(parent/'iteration_4_endpoints.json');budgets=readjson(parent/'iteration_4_budgets.json');protocol=readjson(base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json');graph=protocol['inputs']['graph'];assert sha(graph['path'])==graph['sha256'];bindings[graph['path']]=graph['sha256'];import xml.etree.ElementTree as ET
xml=ET.parse(graph['path']).getroot();nodes={};switches={};adj=defaultdict(list);incoming=defaultdict(list);edges=[];num=lambda text:Fraction(Decimal(text))
for n in xml.find('rr_nodes'):
 t=n.find('timing');r,c=num(t.get('R')),num(t.get('C'));assert r>=0 and c>=0;nodes[int(n.get('id'))]=(r,c,int(n.get('capacity')),n.get('type'))
for s in xml.find('switches'):
 assert s.get('type') in ('buffer','mux','tristate');t=s.find('timing');assert num(t.get('Cinternal','0'))==0;sr,d=num(t.get('R','0')),num(t.get('Tdel','0'));assert sr>=0 and d>=0;switches[int(s.get('id'))]=(sr,d)
for e in xml.find('rr_edges'):
 u,v,sid=int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'));vr,vc,capacity,_=nodes[v];sr,d=switches[sid];delay=(sr+vr/2)*vc+d
 if capacity>0:adj[u].append((v,delay));incoming[v].append((u,delay));edges.append((u,v,delay))
sink=193;selected=(0,4,5,11,61);bs={r['connection_id']:r for r in budgets};assert len(bs)==len(budgets);eps={r['connection_id']:r for r in ep['connections']};assert len(eps)==len(ep['connections']) and set(eps)==set(bs);obligations=[];certs={}
for net in selected:
 rows=[r for r in eps.values() if r['net_id']==net and r['sink']==sink];assert rows;assert len({r['source'] for r in rows})==1
 # One tightest connection per NET suffices for the necessary capacity cut.
 chosen=min(rows,key=lambda r:Fraction(*bs[r['connection_id']]['exact_delay_s']));b=bs[chosen['connection_id']];assert all(chosen[k]==b[k] for k in ('net_id','source','sink'));source=chosen['source'];budget=Fraction(*b['exact_delay_s'])
 if source not in certs:
  distances={source:Fraction(0)};queue=[(Fraction(0),source)]
  while queue:
   value,u=heapq.heappop(queue)
   if distances[u]!=value:continue
   for v,d in adj[u]:
    new=value+d
    if v not in distances or new<distances[v]:distances[v]=new;heapq.heappush(queue,(new,v))
  # Independently validate inequalities/closure and tight source paths. This
  # rejects arbitrary lower estimates and disconnected finite zero-cost cycles.
  tight=defaultdict(list)
  for u,v,d in edges:
   if u in distances:
    assert v in distances and distances[v]<=distances[u]+d
    if distances[v]==distances[u]+d:tight[u].append(v)
  reached={source};todo=deque([source])
  while todo:
   for v in tight[todo.popleft()]:
    if v not in reached:reached.add(v);todo.append(v)
  assert reached==set(distances) and distances[source]==0;certs[source]=distances
  (out/f'source_{source}_distances.json').write_text(json.dumps({str(n):[d.numerator,d.denominator] for n,d in distances.items()})+'\n')
 distances=certs[source];sr,sc,_,_=nodes[source];initial=sr*sc/2;assert nodes[sink][3]=='SINK';assert incoming[sink] and all(nodes[u][3]=='IPIN' for u,d in incoming[sink]);options=sorted({u for u,d in incoming[sink] if u in distances and initial+distances[u]+d<=budget});obligations.append({'net_id':net,'connection_id':chosen['connection_id'],'source':source,'sink':sink,'exact_budget_s':[budget.numerator,budget.denominator],'budget_feasible_terminal_ipins':options})
pins=set().union(*(r['budget_feasible_terminal_ipins'] for r in obligations));capacity=sum(nodes[n][2] for n in pins);assert pins=={255,259,263,267};assert capacity==4<len(selected);assert all(sha(p)==h for p,h in bindings.items())
(out/'verification.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'inputs_sha256':bindings,'obligations':obligations,'distance_certificates_sha256':{p.name:sha(p) for p in out.glob('source_*_distances.json')},'required_distinct_net_uses':5,'reachable_terminal_ipin_capacity':capacity,'raw_node_fixed_budget_capacity_infeasible':True,'scope':'Independent originalXML Fraction graph and certified exact shortest delays. Each distinct NET must occupy a terminal IPIN from these necessary sets; capacity4 cannot satisfy five NETs. Proves infeasibility only for these fixed endpoints, baseline-derived connection RC budgets and uniqueNET raw-node capacity model. Not native pin-equivalence/hardware/user-clock infeasibility or STA.'},indent=2)+'\n');print(obligations,capacity)
