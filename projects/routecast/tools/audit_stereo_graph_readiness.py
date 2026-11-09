"""Streaming full graph inventory; additive RC preconditions, not route legality."""
import json,time,hashlib,resource
from pathlib import Path
from collections import Counter
import xml.etree.ElementTree as ET
from path_rc import number
root=Path('experiments/stereo_prospective_validation_2026-10-05')
p=json.loads((root/'protocol.json').read_text());graph=p['inputs']['graph'];start=time.monotonic()
counts=Counter();segments=Counter();switches={};seen=bytearray();timing_cache=set();stack=[];edges=0
with open(graph['path'],'rb') as stream:
 for event,element in ET.iterparse(stream,events=('start','end')):
  if event=='start':stack.append(element);continue
  parent=stack[-2] if len(stack)>1 else None
  if element.tag=='switch' and parent is not None and parent.tag=='switches':
   sid=int(element.attrib['id']);assert sid not in switches
   timing=element.find('timing');assert timing is not None
   kind=element.attrib['type'];r=number(timing.get('R','0'));d=number(timing.get('Tdel','0'));internal=number(timing.get('Cinternal','0'))
   switches[sid]={'type':kind,'buffered':kind in {'mux','tristate','buffer'},'zero_Cinternal':not internal,'timing':dict(timing.attrib)}
  elif element.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   nid=int(element.attrib['id']);assert nid==len(seen),'expected contiguous ascending node IDs';seen.append(1)
   kind=element.attrib['type'];counts[kind]+=1;capacity=int(element.attrib['capacity']);assert capacity>=0
   timing=element.find('timing');assert timing is not None and 'R' in timing.attrib and 'C' in timing.attrib
   key=(timing.attrib['R'],timing.attrib['C'])
   if key not in timing_cache:number(key[0]);number(key[1]);timing_cache.add(key)
   segment=element.find('segment')
   if kind in {'CHANX','CHANY'}:assert segment is not None;segments[int(segment.attrib['segment_id'])]+=1
  elif element.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   a=int(element.attrib['src_node']);b=int(element.attrib['sink_node']);sid=int(element.attrib['switch_id'])
   assert 0<=a<len(seen) and 0<=b<len(seen) and sid in switches
   edges+=1
   if edges%5000000==0:
    (root/'graph_audit_progress.json').write_text(json.dumps({'nodes':len(seen),'edges':edges,'wall_s':time.monotonic()-start})+'\n')
    print('edges',edges,flush=True)
  if parent is not None and parent.tag in {'rr_nodes','rr_edges','switches','segments','block_types','grid','channels'}:
   parent.remove(element);element.clear()
  stack.pop()
h=hashlib.sha256()
with open(graph['path'],'rb') as f:
 for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
assert h.hexdigest()==graph['sha256']
result={'graph_sha256':h.hexdigest(),'nodes':len(seen),'edges':edges,'node_types':dict(counts),'channel_segment_counts':dict(segments),'switches':switches,'all_node_rc_nonnegative':True,'all_edges_reference_known_nodes_switches':True,'buffered_zero_internal_preconditions':all(s['buffered'] and s['zero_Cinternal'] for s in switches.values()),'wall_s':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'scope':'full serialized graph integrity and additive RC switch preconditions; no endpoint, path, cost-index, native timing or route-legality proof'}
(root/'graph_readiness.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
