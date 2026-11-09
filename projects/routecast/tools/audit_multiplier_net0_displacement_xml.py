"""RawXML electrical and unique-NET occupancy audit of avoidance candidates."""
import json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from decimal import Decimal
from fractions import Fraction
from collections import defaultdict,Counter
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';parent=base/'multiplier_rc_net0_displacement_2026-10-06';out=base/'multiplier_net0_displacement_xml_audit_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');hashes=json.loads((parent/'candidate_hashes.json').read_text());assert sha(parent/'receipt.json')==hashes['receipt_sha256'];receipt=json.loads((parent/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items());bindings={str(parent/'receipt.json'):sha(parent/'receipt.json'),str(parent/'candidate_hashes.json'):sha(parent/'candidate_hashes.json')};reports=[];number=lambda x:Fraction(Decimal(x))
for file,h in hashes['candidate_predictions_sha256'].items():
 path=parent/file;assert sha(path)==h;bindings[str(path)]=h;name=file.split('_net_')[0];protocol=base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json';p=json.loads(protocol.read_text());graph=p['inputs']['graph'];assert sha(graph['path'])==graph['sha256'];bindings[graph['path']]=graph['sha256'];bindings[str(protocol)]=sha(protocol);xml=ET.parse(graph['path']).getroot();nodes={};switches={};edges=[]
 for n in xml.find('rr_nodes'):
  t=n.find('timing');nodes[int(n.get('id'))]=(number(t.get('R')),number(t.get('C')),int(n.get('capacity')),n.get('type'))
 for s in xml.find('switches'):
  assert s.get('type') in ('buffer','mux','tristate');t=s.find('timing');assert number(t.get('Cinternal','0'))==0;switches[int(s.get('id'))]=(number(t.get('R','0')),number(t.get('Tdel','0')))
 for e in xml.find('rr_edges'):edges.append((int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))))
 budgetpath=base/'multiplier_moved_rc_budgets_2026-10-06'/name/'step_1_budgets.json';bindings[str(budgetpath)]=sha(budgetpath);bs={r['connection_id']:r for r in json.loads(budgetpath.read_text())};pred=json.loads(path.read_text());assert pred['physical_graph_sha256']==graph['sha256'];assert len(pred['connections'])==len(bs)==len({r['connection_id'] for r in pred['connections']});unions=defaultdict(set)
 for r in pred['connections']:
  b=bs[r['connection_id']];assert all(r[k]==b[k] for k in ('net_id','source','sink'));u=r['source'];res,cap,capacity,_=nodes[u];delay=res*cap/2;seen={u}
  for eid in r['physical_edge_ids']:
   assert type(eid) is int and 0<=eid<len(edges);src,v,sid=edges[eid];assert src==u and v not in seen;vr,vc,capacity,_=nodes[v];assert capacity>0;sr,intrinsic=switches[sid];assert vr>=0 and vc>=0 and sr>=0 and intrinsic>=0;delay+=(sr+vr/2)*vc+intrinsic;u=v;seen.add(v)
  assert u==r['sink'];assert delay<=Fraction(*b['exact_delay_s']);unions[r['net_id']].update(seen)
 occupancy=Counter(n for union in unions.values() for n in union);assert dict(occupancy)=={int(n):v for n,v in pred['node_occupancy'].items()};overused=[{'node':n,'type':nodes[n][3],'capacity':nodes[n][2],'occupancy':v,'owner_nets':[net for net,union in unions.items() if n in union]} for n,v in occupancy.items() if v>nodes[n][2]];report={'candidate':file,'connections':len(bs),'all_xml_rc_within_fixed_budget':True,'overused_nodes':overused,'overflow':sum(x['occupancy']-x['capacity'] for x in overused)};reports.append(report);print(report,flush=True)
assert all(sha(p)==h for p,h in bindings.items());(out/'verification.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'inputs_sha256':bindings,'results':reports,'scope':'Independent rawXML Decimal/Fraction connection expansion RC, path continuity/cycle/terminal and unique-NET occupancy. Not native STA or placement pin legality. No transaction publication.'},indent=2)+'\n')
