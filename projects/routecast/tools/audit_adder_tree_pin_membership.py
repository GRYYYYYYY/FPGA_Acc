"""Independent direct RR pin membership for all extracted physical pins."""
import json,time,hashlib,argparse
from pathlib import Path
from array import array
from collections import defaultdict
import xml.etree.ElementTree as ET
parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();root=Path('experiments/adder_tree_family_endpoints_2026-10-06')/args.design;out=Path('experiments/adder_tree_family_pin_membership_2026-10-06')/args.design;out.parent.mkdir(exist_ok=True);out.mkdir();(out/'source').mkdir();(out/'source'/Path(__file__).name).write_bytes(Path(__file__).read_bytes())
protocol=json.loads((root/'protocol.json').read_text());mapping=json.loads((root/'mapping.json').read_text());graph=protocol['inputs']['rr_graph'];start=time.monotonic();frontend_receipt=json.loads((root/'receipt.json').read_text());mapping_hash=hashlib.sha256((root/'mapping.json').read_bytes()).hexdigest();assert mapping_hash==frontend_receipt['outputs']['mapping.json'];assert hashlib.sha256((root/'protocol.json').read_bytes()).hexdigest()==frontend_receipt['protocol_sha256'];source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
required={(p['rr_node'],p['physical_pin_ptc'],p['role']) for p in mapping['pin_details']}
classes={v[0] for v in required};pools=defaultdict(set);types=array('B');ptcs=array('I');capacities=array('I');owners={};stack=[];edges=0
kinds={'SOURCE':1,'SINK':2,'OPIN':3,'IPIN':4,'CHANX':5,'CHANY':6}
with open(graph['path'],'rb') as f:
 for event,element in ET.iterparse(f,events=('start','end')):
  if event=='start':stack.append(element);continue
  parent=stack[-2] if len(stack)>1 else None
  if element.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   assert int(element.attrib['id'])==len(types)
   kind=kinds[element.attrib['type']];loc=element.find('loc');assert loc is not None
   types.append(kind);ptcs.append(int(loc.attrib['ptc']));capacities.append(int(element.attrib['capacity']))
  elif element.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   a=int(element.attrib['src_node']);b=int(element.attrib['sink_node']);edges+=1
   endpoint=pin=None
   if types[a]==1 and types[b]==3:endpoint,pin=a,b
   elif types[a]==4 and types[b]==2:endpoint,pin=b,a
   if endpoint in classes:
    assert capacities[pin]==1,'non-unit pin unsupported'
    if pin in owners:assert owners[pin]==endpoint,'pin belongs to multiple requested classes'
    owners[pin]=endpoint;pools[endpoint].add(ptcs[pin])
   if edges%5000000==0:
    (out/'pin_audit_progress.json').write_text(json.dumps({'edges':edges,'wall_s':time.monotonic()-start})+'\n');print('edges',edges,flush=True)
  if parent is not None and parent.tag in {'rr_nodes','rr_edges','switches','segments','block_types','grid','channels'}:parent.remove(element);element.clear()
  stack.pop()
assert edges>0 and len(types)>0
for endpoint,ptc,role in required:
 assert types[endpoint]==(1 if role=='SOURCE' else 2) and ptc in pools[endpoint]
for endpoint in classes:assert len(pools[endpoint])==capacities[endpoint],('class pin count',endpoint)
h=hashlib.sha256()
with open(graph['path'],'rb') as f:
 for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
assert h.hexdigest()==graph['sha256']
assert hashlib.sha256((root/'mapping.json').read_bytes()).hexdigest()==mapping_hash;assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==source_hash
result={'mapping_sha256':mapping_hash,'source_sha256':source_hash,'rr_nodes':len(types),'rr_edges':edges,'mapped_pin_details':len(mapping['pin_details']),'distinct_required_class_pin_roles':len(required),'requested_classes':len(classes),'all_required_direct_pin_memberships_verified':True,'all_requested_class_physical_pin_counts_match_capacity':True,'graph_sha256':h.hexdigest(),'wall_s':time.monotonic()-start,'scope':'all extracted pin_details including exclusions, direct RR membership and requested class capacity; not routing reachability, pin assignment, native QoR or full graph owner uniqueness'}
(out/'pin_membership_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
