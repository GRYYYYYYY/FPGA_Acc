"""Electrical class parity and malformed-input rejection versus streaming read."""
import json,tempfile,random
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
from buffered_rc_node_classes import read
from buffered_rc_from_tree import read_tree
rng=random.Random(33)
with tempfile.TemporaryDirectory(prefix='routecast_tree_') as td:
 f=Path(td)/'graph.xml'
 for trial in range(120):
  root=ET.Element('rr_graph');nodes=ET.SubElement(root,'rr_nodes');switches=ET.SubElement(root,'switches')
  for i in range(rng.randrange(1,40)):
   n=ET.SubElement(nodes,'node',id=str(i));ET.SubElement(n,'timing',R=str(rng.randrange(10)/10),C=str(rng.randrange(10)/10000))
  for i in range(4):
   n=ET.SubElement(switches,'switch',id=str(i),type=['mux','buffer','tristate'][i%3]);ET.SubElement(n,'timing',R=str(i),Tdel=str(i/1000),Cinternal='0')
  f.write_bytes(ET.tostring(root));assert read(f)[:3]==read_tree(ET.parse(f).getroot())
 failures=0
 for kind in ['node_id','missing_timing','switch_id','switch_type','internal_cap']:
  bad=ET.fromstring(ET.tostring(root))
  if kind=='node_id':bad.find('rr_nodes/node').set('id','1')
  if kind=='missing_timing':n=bad.find('rr_nodes/node');n.remove(n.find('timing'))
  if kind=='switch_id':bad.find('switches/switch').set('id','-1')
  if kind=='switch_type':bad.find('switches/switch').set('type','pass_gate')
  if kind=='internal_cap':bad.find('switches/switch/timing').set('Cinternal','.1')
  f.write_bytes(ET.tostring(bad))
  for fn in [lambda:read(f),lambda:read_tree(bad)]:
   try:fn()
   except ValueError:failures+=1
   else:raise AssertionError(kind)
p=Path(__file__).resolve().parents[1]/'experiments/buffered_rc_tree_contract_2026-10-07';p.mkdir();(p/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),implementation_sha256=sha(Path(__file__).with_name('buffered_rc_from_tree.py')),random_graphs=120,both_parser_invalid_rejections=failures,scope='Exact electrical payload parity, same key invalid cases; caller graph identity validation remains necessary.'),indent=2)+'\n');print(failures)
