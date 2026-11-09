"""Compare actual archived native terminal paths to diagnostic fixed budgets."""
import json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from collections import defaultdict
from audit_native_route import NET,NODE
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'multiplier_native_terminal_budget_compare_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');proofroot=base/'multiplier_terminal_cut_xml_certificate_2026-10-06';proof=json.loads((proofroot/'verification.json').read_text());assert sha(proofroot/'verification.json')=='feedab2772a2b09f1a4388c8546b573707b4afcd396a6d88ac924b59786ef200';assert all(sha(p)==h for p,h in proof['inputs_sha256'].items());graph=next(p for p in proof['inputs_sha256'] if p.endswith('rr_graph.xml'));route=root/'work/multiplier_persistent_search_live_swap_2026-10-06/mult_6x6/00_off/design.route';priorroot=base/'multiplier_persistent_search_live_swap_2026-10-06/mult_6x6';prior=json.loads((priorroot/'receipt.json').read_text());truth=next(r for r in prior['results'] if r['run']==0 and r['mode']=='off');assert sha(route)==truth['route_sha256'];protocol=json.loads((priorroot/'protocol.json').read_text());assert sha(priorroot/'protocol.json')==prior['protocol_sha256'];assert protocol['inputs']['rr_graph']['sha256']==sha(graph);placement=root/'work/multiplier_persistent_search_live_swap_2026-10-06/mult_6x6/00_off/design.place';assert sha(placement)==sha(base/'multiplier_placement_swap_2026-10-06/mult_6x6/swapped.place');text=route.read_text();assert 'Placement_ID: SHA256:'+sha(placement) in text
xml=ET.parse(graph).getroot();number=lambda s:Fraction(Decimal(s));nodes={};switches={};arcs=defaultdict(list)
for n in xml.find('rr_nodes'):
 t=n.find('timing');nodes[int(n.get('id'))]=(number(t.get('R')),number(t.get('C')),n.get('type'))
for s in xml.find('switches'):
 assert s.get('type') in ('buffer','mux','tristate');t=s.find('timing');assert number(t.get('Cinternal','0'))==0;switches[int(s.get('id'))]=(number(t.get('R','0')),number(t.get('Tdel','0')))
for eid,e in enumerate(xml.find('rr_edges')):arcs[(int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id')))].append(eid)
net=None;prefix={};current=None;sw=None;records=[];obligations={r['net_id']:r for r in proof['obligations']};selected={};netnodes=defaultdict(set)
for line in text.splitlines():
 match=NET.match(line)
 if match:net=int(match[1]);prefix={};current=None;sw=None;continue
 match=NODE.match(line)
 if not match:
  assert not line.lstrip().startswith('Node:');continue
 nid,kind,newswitch=int(match[1]),match[2],int(match[3]);assert nodes[nid][2]==kind;netnodes[net].add(nid)
 if kind=='SOURCE':
  assert not prefix;r,c,_=nodes[nid];state=(nid,(),(nid,),r*c/2)
 elif nid in prefix and kind!='SINK':state=prefix[nid]
 else:
  assert current in prefix;assert arcs[(current,nid,sw)];source,path,nodepath,delay=prefix[current];r,c,_=nodes[nid];sr,intrinsic=switches[sw];state=(source,path+(min(arcs[(current,nid,sw)]),),nodepath+(nid,),delay+(sr+r/2)*c+intrinsic)
 prefix[nid]=state;current=nid;sw=newswitch
 if kind=='SINK' and net in obligations and nid==193:
  source,path,nodepath,delay=state;o=obligations[net];assert source==o['source'];assert net not in selected;budget=Fraction(*o['exact_budget_s']);selected[net]=nodepath[-2];records.append({'net_id':net,'source':source,'sink':nid,'terminal_ipin':nodepath[-2],'physical_edge_ids':list(path),'exact_native_path_expansion_s':[delay.numerator,delay.denominator],'fixed_predictor_budget_s':o['exact_budget_s'],'exceeds_predictor_budget':delay>budget,'excess_ns':float((delay-budget)*10**9)})
assert set(selected)==set(obligations) and len(set(selected.values()))==5;assert sha(route)==truth['route_sha256'];assert sha(graph)==protocol['inputs']['rr_graph']['sha256']
(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'graph_sha256':sha(graph),'native_route_sha256':sha(route),'native_receipt_sha256':sha(priorroot/'receipt.json'),'placement_sha256':sha(placement),'certificate_sha256':sha(proofroot/'verification.json'),'results':records,'distinct_native_terminal_ipins':len(set(selected.values())),'scope':'Archived successful native route, exact serializedXML buffered connection path expansion, selected singleton NET/SINK paths. Parallel identical arc tuple chooses minimum physical edge ID; same switch and nodes imply same delay. No route-tree STA/branch load/native float delay parity, fresh routing/timing or user-clock feasibility claim.'},indent=2)+'\n');print(records,flush=True)
