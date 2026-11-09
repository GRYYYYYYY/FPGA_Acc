"""Exact uniform additive budget slack for necessary terminal matching only."""
import json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from decimal import Decimal
from terminal_capacity_gate import terminal_cut
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'multiplier_terminal_budget_slack_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');proofroot=base/'multiplier_terminal_cut_xml_certificate_2026-10-06';p=proofroot/'verification.json';assert sha(p)=='feedab2772a2b09f1a4388c8546b573707b4afcd396a6d88ac924b59786ef200';proof=json.loads(p.read_text());assert all(sha(n)==h for n,h in proof['inputs_sha256'].items());assert all(sha(proofroot/n)==h for n,h in proof['distance_certificates_sha256'].items());graph=next(n for n in proof['inputs_sha256'] if n.endswith('rr_graph.xml'));xml=ET.parse(graph).getroot();num=lambda s:Fraction(Decimal(s));nodes={};switches={}
for n in xml.find('rr_nodes'):
 t=n.find('timing');nodes[int(n.get('id'))]=(num(t.get('R')),num(t.get('C')),int(n.get('capacity')))
for s in xml.find('switches'):
 assert s.get('type') in ('buffer','mux','tristate');t=s.find('timing');assert num(t.get('Cinternal','0'))==0;switches[int(s.get('id'))]=(num(t.get('R','0')),num(t.get('Tdel','0')))
sink=proof['obligations'][0]['sink'];incoming=[]
for e in xml.find('rr_edges'):
 if int(e.get('sink_node'))!=sink:continue
 u=int(e.get('src_node'));sid=int(e.get('switch_id'));vr,vc,capacity=nodes[sink];sr,d=switches[sid]
 if capacity>0:incoming.append((u,(sr+vr/2)*vc+d))
caps={u:nodes[u][2] for u,d in incoming};thresholds={Fraction(0)};requirements=[]
for o in proof['obligations']:
 dist={int(n):Fraction(*d) for n,d in json.loads((proofroot/f"source_{o['source']}_distances.json").read_text()).items()};r,c,_=nodes[o['source']];initial=r*c/2;budget=Fraction(*o['exact_budget_s']);needed={}
 for node,delay in incoming:
  if node not in dist:continue
  slack=max(Fraction(0),initial+dist[node]+delay-budget)
  if node not in needed or slack<needed[node]:needed[node]=slack
  thresholds.add(slack)
 requirements.append((o['net_id'],needed))
checks=[];first=None
for slack in sorted(thresholds):
 result=terminal_cut([(net,{n for n,v in needed.items() if v<=slack}) for net,needed in requirements],caps);checks.append({'slack_s':[slack.numerator,slack.denominator],'result':result})
 if result['status']=='NO_CUT':first=slack;break
assert first is not None and first>0
# Construct an actual capacitated terminal assignment at the first threshold.
choices=[(net,[n for n,v in needed.items() if v<=first]) for net,needed in requirements]
def match(i,used,assignment):
 if i==len(choices):return dict(assignment)
 net,pins=choices[i]
 for pin in sorted(pins):
  if used.get(pin,0)>=caps[pin]:continue
  used[pin]=used.get(pin,0)+1;assignment[net]=pin;found=match(i+1,used,assignment)
  if found is not None:return found
  used[pin]-=1;assignment.pop(net)
 return None
assignment=match(0,{},{});assert assignment is not None;assert all(sha(n)==h for n,h in proof['inputs_sha256'].items())
(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'certificate_sha256':sha(p),'gate_sha256':sha(root/'tools/terminal_capacity_gate.py'),'minimum_uniform_additive_terminal_slack_s':[first.numerator,first.denominator],'minimum_uniform_additive_terminal_slack_ns':float(first*10**9),'terminal_assignment':assignment,'threshold_checks':checks,'scope':'Diagnostic exact minimum uniform additive slack sufficient for only five certified terminal obligations matching. Required lower bound on uniform relaxation for any complete routing; terminal matching does not certify internal capacities/tree/native pin equivalence or STA. No experiment budgets were changed.'},indent=2)+'\n');print(first,float(first*10**9),assignment)
