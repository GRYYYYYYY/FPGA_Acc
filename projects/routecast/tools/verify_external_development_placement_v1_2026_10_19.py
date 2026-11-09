"""Independent fixed-profile grid, block coverage and slot/capacity placement audit."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 root=R/'experiments/prospective_external_family_development_place_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);assert r['exit_code']==0 and r['placement_rows']==509 and not r['new_route_labels'];pp=root/'protocol.json';p=read(pp)
 for d in [r,p]:
  for f,h in d['bindings'].items():assert sha(f)==h
 arch=Path(p['command'][1]);a=ET.parse(arch).getroot();layout=a.find('layout/auto_layout');assert layout is not None and layout.attrib=={'aspect_ratio':'1.0'};rules={e.tag+':'+e.get('type'):dict(e.attrib) for e in layout};assert len(rules)==5 and rules['fill:clb']==dict(type='clb',priority='10') and rules['perimeter:io']==dict(type='io',priority='101') and rules['corners:EMPTY']==dict(type='EMPTY',priority='102');assert rules['col:dsp_top']==dict(type='dsp_top',startx='6',starty='1',repeatx='16',priority='20') and rules['col:memory']==dict(type='memory',startx='2',starty='1',repeatx='16',priority='20');tiles={t.get('name'):t for t in a.findall('tiles/tile')};assert set(tiles)=={'clb','io','dsp_top','memory'};assert int(tiles['dsp_top'].get('height'))==4 and int(tiles['memory'].get('height'))==2
 net=root/'design.net';blocks=ET.parse(net).getroot().findall('block');expected={b.get('name'):(i,b.get('instance').split('[')[0]) for i,b in enumerate(blocks)};assert len(expected)==len(blocks)==509 and Counter(t for i,t in expected.values())==dict(clb=433,io=76);place=root/'source.place';text=place.read_text();assert 'SHA256:'+sha(net) in text;match=re.search(r'Array size: (\d+) x (\d+) logic blocks',text);width,height=map(int,match.groups());assert (width,height)==(25,25);seen=set();slots=set();counts=Counter()
 for line in text.splitlines():
  t=line.split()
  if not t or t[0].startswith('#') or len(t)!=6 or not t[-1].startswith('#'):continue
  name=t[0];x,y,sub,layer=map(int,t[1:5]);idx=int(t[-1][1:]);assert name in expected and name not in seen;seen.add(name);index,kind=expected[name];assert idx==index and 0<=x<width and 0<=y<height and layer==0;slot=(x,y,sub,layer);assert slot not in slots;slots.add(slot);counts[kind]+=1
  if kind=='io':
   assert x in (0,width-1) or y in (0,height-1);assert not (x in (0,width-1) and y in (0,height-1));assert 0<=sub<int(tiles['io'].find('sub_tile').get('capacity'))
  else:
   assert kind=='clb' and 0<x<width-1 and 0<y<height-1 and sub==0
   # Col rule repeats whole multiheight tiles, with perimeter priority higher.
   # Incomplete last tile is omitted; the existing lower-priority fill remains.
   for col in layout.findall('col'):
    start,repeat=int(col.get('startx')),int(col.get('repeatx'));h=int(tiles[col.get('type')].get('height'));starty=int(col.get('starty'));oncol=x>=start and (x-start)%repeat==0
    if oncol and y>=starty:
     anchor=starty+((y-starty)//h)*h;assert anchor+h>height-1,'CLB occupies complete reserved column tile'
 assert seen==set(expected) and counts==dict(clb=433,io=76);assert not list(root.glob('*.route'));log=(root/'place.log').read_text();assert 'VPR succeeded' in log and log.count('Completed placement consistency check successfully.')>=2
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL509_BLOCKS_FIXED_XML_GRID_TYPES_CAPACITY_SLOTS_AND_NATIVE_CHECKS_VERIFIED',blocks=509,CLBs=433,IO_blocks=76,grid=[width,height],unique_slots=len(slots),bindings={str(p):sha(p) for p in [rp,pp,net,place,root/'place.log',arch,Path(__file__).resolve()]},scope='Independent exact current architecture-profile rules for this grid, original block identity/index coverage, unique slots/layer/capacity and final native consistency transcript. Not a generic architecture parser, routing legality, placement QoR gain, static timing closure or strict unseen-family admission.'),f,indent=2)
 print('INDEPENDENT_DEVELOPMENT_PLACE_PASS',len(seen),dict(counts),width,height)
if __name__=='__main__':main()
