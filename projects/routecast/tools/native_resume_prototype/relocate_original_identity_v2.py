"""Guarded coordinate relocation of a native-captured ORIGINAL packed identity.

Never applies to post-routing identity changes. Caller must supply native capture
provenance; final routing still requires original-native FULL/STA validation.
"""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha

def placement(path):
 result={};ids=set();sites=set()
 for line in Path(path).read_text().splitlines():
  m=re.fullmatch(r'(\S+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+#(\d+)\s*',line)
  if not m:continue
  name=m[1];x,y,sub,layer,bid=map(int,m.groups()[1:]);site=(x,y,layer,sub)
  if name in result or bid in ids or site in sites:raise ValueError('duplicate placement identity/site')
  result[name]=(x,y,layer,sub,bid);ids.add(bid);sites.add(site)
 if not result:raise ValueError('empty placement')
 return result

class OriginalIdentityRelocator:
 def __init__(self,endpoint,table,capture_receipt,graph):
  self.endpoint=Path(endpoint);self.table=Path(table);self.graph=Path(graph);proof=json.loads(Path(capture_receipt).read_text());meta=json.loads(self.endpoint.read_text())
  if proof['identity_capture_exit_code']!=1 or not all(sha(p)==h for p,h in proof['bindings'].items()):raise ValueError('invalid native capture provenance')
  # Capture command must refer to the original copied packed NET and place,
  # rather than an identity acquired after route-driven pin/NET changes.
  work=Path(capture_receipt).parent
  if self.table.resolve()!=(work/'identity.jsonl').resolve() or proof.get('identity_table_sha256')!=sha(self.table):raise ValueError('native capture table binding mismatch')
  if sha(work/'design.net')!=meta['inputs']['net']['sha256'] or sha(work/'design.place')!=meta['inputs']['place']['sha256']:raise ValueError('capture is not original packed endpoint state')
  if str(self.graph)!=proof['command'][proof['command'].index('--read_rr_graph')+1] or sha(self.graph)!=meta['graph_sha256']:raise ValueError('capture graph mismatch')
  self.meta=meta;self.old=placement(meta['inputs']['place']['path']);self.rows=list(map(json.loads,self.table.read_text().splitlines()));self.bindings={**proof['bindings'],str(self.endpoint):sha(self.endpoint),str(self.table):sha(self.table),str(capture_receipt):sha(capture_receipt),str(self.graph):sha(self.graph)}
  names=set();netids=set()
  for row in self.rows:
   if row['name'] in names or row['net_id'] in netids:raise ValueError('duplicate native NET identity')
   names.add(row['name']);netids.add(row['net_id']);indices=set()
   for pin in row['pins']:
    if pin['index'] in indices:raise ValueError('duplicate native pin index')
    indices.add(pin['index']);old=self.old[pin['block']]
    if (pin['x'],pin['y'],pin['layer'])!=old[:3]:raise ValueError('capture pin/placement mismatch')
  self.grid={}
  for _,e in ET.iterparse(self.graph,events=('end',)):
   if e.tag=='grid_loc':
    a=e.attrib;site=tuple(int(a[k]) for k in ('x','y','layer'));self.grid[site]=tuple(int(a[k]) for k in ('block_type_id','width_offset','height_offset'))
   if e.tag=='grid':break
  if not self.grid:raise ValueError('RR grid metadata unavailable')
  self._validate()
 def _validate(self):
  if not all(sha(p)==h for p,h in self.bindings.items()):raise ValueError('capture dependency changed')
 def relocate(self,endpoint,destination):
  self._validate();endpoint=Path(endpoint);destination=Path(destination);meta=json.loads(endpoint.read_text());before=sha(endpoint)
  if meta['inputs']['net']!=self.meta['inputs']['net'] or meta['net_names']!=self.meta['net_names'] or meta['graph_sha256']!=self.meta['graph_sha256']:raise ValueError('original packed NET/graph changed')
  if not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('endpoint input binding changed')
  new=placement(meta['inputs']['place']['path'])
  if new.keys()!=self.old.keys():raise ValueError('placement block set changed')
  for name,old in self.old.items():
   target=new[name]
   if target[3:]!=old[3:] or self.grid.get(target[:3])!=self.grid.get(old[:3]) or target[:3] not in self.grid:raise ValueError('block identity/subtile/tile type changed')
  rows=json.loads(json.dumps(self.rows))
  for row in rows:
   for pin in row['pins']:pin['x'],pin['y'],pin['layer']=new[pin['block']][:3]
  text=''.join(json.dumps(row,separators=(',',':'))+'\n' for row in rows)
  self._validate()
  if sha(endpoint)!=before or not all(sha(v['path'])==v['sha256'] for v in meta['inputs'].values()):raise ValueError('endpoint changed during relocation')
  with destination.open('x') as stream:stream.write(text)
  return dict(bindings={**self.bindings,str(endpoint):before},output_sha256=sha(destination),native_recapture_performed=False,scope='Serial identical original packed NET and graph, same block IDs/subtiles/tile types/offsets; coordinates only. No route acceptance or concurrent publication guarantee.')
