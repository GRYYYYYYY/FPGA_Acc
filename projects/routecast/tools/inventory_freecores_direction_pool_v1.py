"""Full RR direction-pooling feasibility inventory; no search ablation."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/freecores_direction_pool_inventory_v1_2026-10-08';out.mkdir();bindings={str(Path(__file__)):sha(Path(__file__))};rows=[]
for name in ['8051','xtea']:
 endpoint=R/'experiments/freecores_native_demand_v1_2026-10-08'/name/'endpoints.json';ep=json.loads(endpoint.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(endpoint)]=sha(endpoint);bindings[str(graph)]=ep['graph_sha256'];groups=defaultdict(Counter);directions=Counter();stack=[]
 for event,node in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(node);continue
  parent=stack[-2] if len(stack)>1 else None
  if node.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   kind=node.get('type');cap=int(node.get('capacity'))
   if kind in ('CHANX','CHANY') and cap>0:
    loc=node.find('loc');seg=node.find('segment');timing=node.find('timing');direction=node.get('direction');assert direction in ('INC_DIR','DEC_DIR','BI_DIR','NO_DIR')
    key=(kind,cap,tuple(loc.get(k,'0') for k in ('xlow','xhigh','ylow','yhigh','layer')),tuple(sorted(seg.attrib.items())) if seg is not None else (),tuple(sorted(timing.attrib.items())) if timing is not None else ())
    groups[key][direction]+=1;directions[direction]+=1
  if node.tag in ('node','edge','switch','segment') and parent is not None and parent.tag in ('rr_nodes','rr_edges','switches','segments'):parent.remove(node);node.clear()
  stack.pop()
 both=[g for g in groups.values() if g['INC_DIR'] and g['DEC_DIR']]
 rows.append(dict(name=name,positive_channel_nodes=sum(directions.values()),directions=dict(directions),exact_span_type_segment_capacity_RC_groups=len(groups),groups_with_both_polarities=len(both),nodes_in_both_polarity_groups=sum(sum(g.values()) for g in both),scope='Track ID omitted, channel axis/full bounds/layer/segment/capacity/R/C retained. Counts only: no topology/cost/pressure changes, no direction search ablation or accuracy proof.'))
assert all(sha(k)==h for k,h in bindings.items())
(out/'inventory.json').write_text(json.dumps(dict(bindings=bindings,rows=rows),indent=2)+'\n');print(json.dumps(rows,indent=2))
