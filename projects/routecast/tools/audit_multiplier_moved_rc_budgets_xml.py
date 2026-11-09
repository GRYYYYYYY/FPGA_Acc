"""Independent raw XML paths/RC oracle; no prepared electrical/CSR import."""
import json,shutil,xml.etree.ElementTree as ET
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';budgets=base/'multiplier_moved_rc_budgets_2026-10-06';out=base/'multiplier_moved_rc_budget_xml_audit_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');receipt=json.loads((budgets/'receipt.json').read_text());assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items());bindings={str(budgets/'receipt.json'):sha(budgets/'receipt.json')};reports=[]
num=lambda text:Fraction(Decimal(text))
for w in range(4,10):
 name=f'mult_{w}x{w}';protocol=base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/protocol.json';p=json.loads(protocol.read_text());graph=p['inputs']['graph'];assert sha(graph['path'])==graph['sha256'];bindings[graph['path']]=graph['sha256'];bindings[str(protocol)]=sha(protocol)
 xml=ET.parse(graph['path']).getroot();nodes={};switches={};edges=[]
 for n in xml.find('rr_nodes'):
  timing=n.find('timing');r=num(timing.attrib['R']);c=num(timing.attrib['C']);assert r>=0 and c>=0;nodes[int(n.attrib['id'])]=(r,c,int(n.attrib['capacity']))
 for s in xml.find('switches'):
  assert s.attrib['type'] in ('mux','buffer','tristate');t=s.find('timing');assert num(t.get('Cinternal','0'))==0;sr=num(t.get('R','0'));d=num(t.get('Tdel','0'));assert sr>=0 and d>=0;switches[int(s.attrib['id'])]=(sr,d)
 for e in xml.find('rr_edges'):edges.append((int(e.attrib['src_node']),int(e.attrib['sink_node']),int(e.attrib['switch_id'])))
 for step in (0,1):
  row=next(x for x in receipt['steps'] if x['design']==name and x['step']==step);file=budgets/name/f'step_{step}_budgets.json';assert sha(file)==row['budget_sha256'];bindings[str(file)]=sha(file)
  predfile=base/'multiplier_family_predictions_2026-10-06'/name/'sparse_reset/prediction.json' if step==0 else base/'multiplier_moved_incremental_search_2026-10-06'/name/'prediction.json';assert sha(predfile)==row['reference_prediction_sha256'];bindings[str(predfile)]=sha(predfile);pred=json.loads(predfile.read_text());actual={r['connection_id']:r for r in pred['connections']};rows=json.loads(file.read_text());assert set(actual)=={r['connection_id'] for r in rows};checked=0
  for b in rows:
   r=actual[b['connection_id']];assert all(r[k]==b[k] for k in ('net_id','source','sink'));node=r['source'];res,c,cap=nodes[node];delay=res*c/2;seen={node}
   for eid in r['physical_edge_ids']:
    assert type(eid) is int and 0<=eid<len(edges);u,v,sid=edges[eid];assert u==node and v not in seen;vr,vc,capacity=nodes[v];assert capacity>0;sr,intrinsic=switches[sid];delay+=intrinsic+(sr+vr/2)*vc;node=v;seen.add(v)
   assert node==r['sink'];assert delay==Fraction(*b['exact_delay_s'])==Fraction(b['scaled_integer_budget'],row['integer_scale']);checked+=1
  reports.append({'design':name,'step':step,'connections_exact_xml_rc_and_path_checked':checked});print(reports[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items());assert all(sha(p)==h for p,h in receipt['inputs_sha256'].items())
(out/'verification.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'inputs_sha256':bindings,'steps':reports,'total_connections':sum(x['connections_exact_xml_rc_and_path_checked'] for x in reports),'scope':'Independent Decimal/Fraction rawXML buffered Cinternal0 connection expansion delay; validates physical edge IDs, continuity, cycles, sink and destination capacity. Not route-tree branch loading, native STA, clock budgets, placement/pin legality or full move transaction.'},indent=2)+'\n')
