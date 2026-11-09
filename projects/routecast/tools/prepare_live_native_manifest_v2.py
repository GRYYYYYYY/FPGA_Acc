"""Current-arm native pin/endpoint manifest, preserving duplicate sinks individually."""
import json,xml.etree.ElementTree as E
from pathlib import Path
from collections import defaultdict,deque
from pre_route_endpoints import sha

def prepare(endpoint,destination):
 ep=json.loads(Path(endpoint).read_text());assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());records=[json.loads(l) for l in Path(ep['inputs']['native_identity']['path']).read_text().splitlines()];native={r['name']:r for r in records};assert len(native)==len(records)
 lookup={};nodes=0;edges=0;parents={};last_source=-1
 for event,node in E.iterparse(ep['inputs']['graph']['path'],events=('start','end')):
  if event=='start':
   if node.tag in ['rr_nodes','rr_edges']:parents[node.tag]=node
   continue
  if node.tag=='node':
   assert int(node.get('id'))==nodes;nodes+=1
   if node.get('type') in {'SOURCE','SINK'}:
    loc=node.find('loc');key=(node.get('type'),int(loc.get('xlow')),int(loc.get('ylow')),int(loc.get('layer','0')),int(loc.get('ptc')));assert key not in lookup;lookup[key]=int(node.get('id'))
   node.clear()
   if nodes%1024==0:parents['rr_nodes'].clear()
  elif node.tag=='edge':
   source=int(node.get('src_node'));sink=int(node.get('sink_node'));assert 0<=source<nodes and 0<=sink<nodes and source>=last_source;last_source=source;edges+=1;node.clear()
   if edges%1024==0:parents['rr_edges'].clear()
 assert nodes and edges
 lines=[f"G {nodes} {edges} {len(ep['connections'])}\n"];cidnet={};groups=defaultdict(list)
 for r in records:lines.append(f"N {r['net_id']} {int(r['ignored'])} {len(r['pins'])}\n")
 for q in ep['connections']:groups[q['net_id']].append(q)
 for net,qs in sorted(groups.items()):
  r=native[ep['net_names'][str(net)]];assert not r['ignored'];pins=r['pins'];assert [p['index'] for p in pins]==list(range(len(pins)))
  def terminal(p,kind):return lookup[kind,p['x'],p['y'],p['layer'],p['class']]
  source=terminal(pins[0],'SOURCE');sinks=defaultdict(deque)
  for p in pins[1:]:sinks[terminal(p,'SINK')].append(p['index'])
  for q in qs:
   assert q['source']==source and sinks[q['sink']];pin=sinks[q['sink']].popleft();cid=q['connection_id'];assert cid not in cidnet;cidnet[cid]=r['net_id'];lines.append(f"Q {cid} {r['net_id']} {pin} {source} {q['sink']}\n")
  assert all(not v for v in sinks.values())
 assert len(cidnet)==len(ep['connections'])
 assert {r['net_id'] for r in records if not r['ignored'] and len(r['pins'])>1}==set(cidnet.values())
 assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values())
 destination=Path(destination);destination.write_text(''.join(lines));return cidnet
