"""Crosscheck explicit native tnodes against packed leaves and complete timing arcs."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_atom_timing_identity_2026-10-06';base=ROOT/'experiments/mux_old_full_timing_graph_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['protocol_sha256']==sha(out/'protocol.json');rows=[]
for row in r['rows']:
 w=row['width'];work=out/f'w{w}';table=work/'atom_identity.jsonl';assert sha(table)==row['identity_sha256']and all(sha(f)==h for f,h in row['inputs'].items());graph=json.loads((base/f'w{w}_timing_graph.json').read_text());mapped={};pins={};leaf={}
 for cluster in ET.parse(work/'design.net').getroot().findall('block'):
  for atom in cluster.iter('block'):
   if atom.get('name')!='open'and not atom.findall('block'):leaf[atom.get('name')]=cluster.get('name')
 for x in map(json.loads,table.read_text().splitlines()):
  assert leaf[x['atom']]==x['cluster'];key=(x['atom'],x['port'],x['bit'],x['net'],x['cluster']);pin=x['atom_pin_id']
  if pin in pins:assert pins[pin]==key
  pins[pin]=key
  if x['node_id']is not None:
   n=x['node_id']
   if n in mapped:assert mapped[n]==key
   mapped[n]=key
 assert set(mapped)=={int(n)for n in graph['nodes']};assert len(pins)==len(mapped)
 counts={}
 for edge in graph['edges'].values():
  u,v=mapped[edge['source']],mapped[edge['sink']];kind=edge['type'];counts[kind]=counts.get(kind,0)+1
  if kind=='INTERCONNECT':assert u[3]==v[3]and u[3]
  elif kind=='PRIMITIVE_COMBINATIONAL':assert u[0]==v[0]and u[1]=='in'and v[1]=='out'
  else:raise AssertionError(kind)
 assert sha(work/'timing_graph.analysis.echo')==row['echo_sha256'];rows.append(dict(width=w,nodes=len(mapped),unique_atom_pins=len(pins),edge_counts=counts,packed_atom_ownership_verified=True))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Native explicit pin identity covers9032nodes, packedleaf ownership and every edge logicalnet/primitive identity crosschecks; RRsite/class and prospective interblockreplacement still pending.'),indent=2)+'\n');print(rows)
