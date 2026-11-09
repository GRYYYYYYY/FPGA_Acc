"""Structural packed-port synchronization audit; not logical equivalence proof."""
import json,shutil,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];base=root/'experiments';out=base/'native_packing_sync_delta_v2_2026-10-06';out.mkdir();shutil.copyfile(Path(__file__),out/'source.py');parent=base/'native_predictor_sync_capture_2026-10-06';proof=json.loads((parent/'receipt.json').read_text());work=root/'work/native_predictor_sync_capture_2026-10-06';old=work/'design.net';new=work/'design.net.post_routing';assert sha(new)==proof['post_routing_netlist_sha256'];original=json.loads((base/'native_zero_pressure_control_2026-10-06/receipt.json').read_text())['inputs']['packed_netlist'];assert sha(old)==original['sha256'];assert sha(parent/'before_sync.route')==proof['before_trace_sha256'];assert sha(parent/'after_sync.route')==proof['after_trace_sha256'];assert (parent/'before_sync.route').read_bytes()==(parent/'after_sync.route').read_bytes()
def parse(file):
 xml=ET.parse(file).getroot();blocks={};ports={};leaves={}
 def visit(block,path):
  identity=(block.get('instance'),block.get('name'));key=path+(identity,);attrs=dict(block.attrib);blocks[key]=attrs
  for role in ('inputs','outputs','clocks'):
   element=block.find(role)
   if element is None:continue
   if list(element):
    for port in element:
     pkey=(key,role,port.tag+':'+str(port.get('name')));assert pkey not in ports;ports[pkey]=(port.text or '').split()
   elif not path:ports[(key,role,'root')]=(element.text or '').split()
  children=block.findall('block')
  if not children and block.get('name')!='open':leaves[key]=attrs
  for child in children:visit(child,key)
 # Root output filename is not a block identity; normalize that metadata only.
 xml.set('name','ROOT');visit(xml,());return blocks,ports,leaves
before,bports,bleaves=parse(old);after,aports,aleaves=parse(new);assert set(before)==set(after);assert set(bports)==set(aports);assert bleaves==aleaves
changes=[]
for key in sorted(bports,key=str):
 a,b=bports[key],aports[key]
 if a==b:continue
 path,role,port=key;assert len(a)==len(b);changes.append({'hierarchy':[{'instance':i,'name':n} for i,n in path],'role':role,'port':port,'depth':len(path)-1,'changed_slots':[{'slot':i,'before':x,'after':y} for i,(x,y) in enumerate(zip(a,b)) if x!=y]})
external=[r for r in changes if r['depth']==1];internal=[r for r in changes if r['depth']>1];blocks_changed=[{'hierarchy':[{'instance':i,'name':n} for i,n in key],'before':before[key],'after':after[key]} for key in before if before[key]!=after[key]]
def external_multiset(ports):
 c=Counter()
 for (path,role,port),tokens in ports.items():
  if len(path)==2 and role=='inputs':c.update(t for t in tokens if t!='open')
 return c
preserved=external_multiset(bports)==external_multiset(aports);assert preserved
(out/'port_changes.json').write_text(json.dumps(changes,indent=2)+'\n');(out/'block_attribute_changes.json').write_text(json.dumps(blocks_changed,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'source_sha256':sha(out/'source.py'),'capture_receipt_sha256':sha(parent/'receipt.json'),'before_packed_sha256':sha(old),'after_packed_sha256':sha(new),'port_changes_sha256':sha(out/'port_changes.json'),'block_attributes_sha256':sha(out/'block_attribute_changes.json'),'blocks':len(before),'primitive_leaf_blocks':len(bleaves),'all_block_hierarchy_and_primitive_leaf_attributes_preserved':True,'all_port_dimensions_preserved':True,'changed_external_ports':len(external),'changed_external_slots':sum(len(r['changed_slots']) for r in external),'changed_internal_ports':len(internal),'changed_internal_slots':sum(len(r['changed_slots']) for r in internal),'external_input_net_multiset_preserved':preserved,'rr_trace_bytes_preserved':True,'scope':'Packed serialized block/port structural delta and external input NET multiset; no formal atom connectivity/functional equivalence or complete in-memory timing-state capture.'},indent=2)+'\n');print(len(external),sum(len(r['changed_slots']) for r in external),len(internal),sum(len(r['changed_slots']) for r in internal),preserved)
