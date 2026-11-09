"""Independent raw XML paths/RC oracle; no prepared electrical/CSR import."""
import sys,json,shutil,xml.etree.ElementTree as ET
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';budgets=base/'multiplier_moved_rc_budgets_2026-10-06';out=base/'multiplier_rc_move_output_xml_audit_2026-10-06'/sys.argv[1];out.mkdir(parents=True);shutil.copyfile(Path(__file__),out/'source.py');receipt=json.loads((budgets/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items());bindings={str(budgets/'receipt.json'):sha(budgets/'receipt.json')};reports=[]
num=lambda text:Fraction(Decimal(text))
for w in [int(sys.argv[1].split('_')[1].split('x')[0])]:
 name=f'mult_{w}x{w}';protocol=base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json';p=json.loads(protocol.read_text());graph=p['inputs']['graph'];assert sha(graph['path'])==graph['sha256'];bindings[graph['path']]=graph['sha256'];bindings[str(protocol)]=sha(protocol)
 xml=ET.parse(graph['path']).getroot();nodes={};switches={};edges=[]
 for n in xml.find('rr_nodes'):
  timing=n.find('timing');r=num(timing.attrib['R']);c=num(timing.attrib['C']);assert r>=0 and c>=0;nodes[int(n.attrib['id'])]=(r,c,int(n.attrib['capacity']))
 for s in xml.find('switches'):
  assert s.attrib['type'] in ('mux','buffer','tristate');t=s.find('timing');assert num(t.get('Cinternal','0'))==0;sr=num(t.get('R','0'));d=num(t.get('Tdel','0'));assert sr>=0 and d>=0;switches[int(s.attrib['id'])]=(sr,d)
 for e in xml.find('rr_edges'):edges.append((int(e.attrib['src_node']),int(e.attrib['sink_node']),int(e.attrib['switch_id'])))
 for step in (0,1):
  row=next(x for x in receipt['steps'] if x['design']==name and x['step']==step);file=budgets/name/f'step_{step}_budgets.json';assert sha(file)==row['budget_sha256'];bindings[str(file)]=sha(file)
  txroot=base/'multiplier_rc_move_transactions_v4_2026-10-06'/name;tx=json.loads((txroot/'receipt.json').read_text());assert all(sha(txroot/n)==h for n,h in tx['outputs_sha256'].items());assert all(sha(p)==h for p,h in tx['inputs_sha256'].items());bindings[str(txroot/'receipt.json')]=sha(txroot/'receipt.json')
  predfile=txroot/f'step_{step}_prediction.json';bindings[str(predfile)]=sha(predfile);pred=json.loads(predfile.read_text());actual={r['connection_id']:r for r in pred['connections']};rows=json.loads(file.read_text());assert len(actual)==len(pred['connections'])==len(rows);assert set(actual)=={r['connection_id'] for r in rows};checked=0
  from collections import defaultdict,Counter
  unions=defaultdict(set)
  for b in rows:
   r=actual[b['connection_id']];assert all(r[k]==b[k] for k in ('net_id','source','sink'));node=r['source'];res,c,cap=nodes[node];delay=res*c/2;seen={node};unions[r['net_id']].add(node)
   for eid in r['physical_edge_ids']:
    assert type(eid) is int and 0<=eid<len(edges);u,v,sid=edges[eid];assert u==node and v not in seen;vr,vc,capacity=nodes[v];assert capacity>0;sr,intrinsic=switches[sid];delay+=intrinsic+(sr+vr/2)*vc;node=v;seen.add(v)
   assert node==r['sink'];assert delay<=Fraction(b['scaled_integer_budget'],row['integer_scale']);unions[r['net_id']].update(seen);checked+=1
  occupancy=Counter(n for u in unions.values() for n in u);assert dict(occupancy)=={int(n):v for n,v in pred['node_occupancy'].items()};overflow=sum(max(0,v-nodes[n][2]) for n,v in occupancy.items());assert overflow==tx['steps'][step]['final_overflow']
  reports.append({'design':name,'step':step,'connections_exact_xml_rc_and_path_checked':checked,'independent_xml_overflow':overflow});print(reports[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items());assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items())
(out/'verification.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'inputs_sha256':bindings,'steps':reports,'total_connections':sum(x['connections_exact_xml_rc_and_path_checked'] for x in reports),'scope':'Independent Decimal/Fraction rawXML buffered Cinternal0 connection expansion delay; validates physical edge IDs, continuity, cycles, sink and destination capacity. Final union occupancy rebuilt independently. Not route-tree branch loading, native STA, clock budgets, placement/pin legality or full move transaction.'},indent=2)+'\n')
