"""Independent original-XML local feedback selection and complete ledger audit."""
import json,xml.etree.ElementTree as ET
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_local_feedback_verification_v1_2026-10-09';D.mkdir(exist_ok=False)
P=E/'full_ram_local_feedback_v2_2026-10-09';B=E/'full_ram_length_switch_prediction_v1_2026-10-09';F=E/'full_ram_own_excluded_channel_prediction_v1_2026-10-09'
r=json.loads((P/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_LOCAL_FEEDBACK'
for p,h in r['bindings'].items():assert sha(p)==h
old=json.loads((B/'prediction.json').read_text());full=json.loads((F/'prediction.json').read_text());new=json.loads((P/'prediction.json').read_text())
graph=E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml';caps={};edges=[];stack=[]
for event,x in ET.iterparse(graph,events=['start','end']):
 if event=='start':stack.append(x);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if x.tag=='node' and parent=='rr_nodes':caps[int(x.get('id'))]=int(x.get('capacity'))
 if x.tag=='edge' and parent=='rr_edges':edges.append((int(x.get('src_node')),int(x.get('sink_node'))))
 if (x.tag,parent) in [('node','rr_nodes'),('edge','rr_edges')]:stack[-2].remove(x);x.clear()
 stack.pop()
def nodes(c):
 current=c['source'];visited={current}
 for eid in c['physical_edge_ids']:
  a,b=edges[eid];assert a==current and b not in visited and caps[b]>0;visited.add(b);current=b
 assert current==c['sink'];return visited
owners=defaultdict(set)
for c in old['connections']:
 for n in nodes(c):owners[n].add(c['net_id'])
assert {str(n):len(v) for n,v in owners.items()}==old['node_occupancy']
over={n:len(v)-caps[n] for n,v in owners.items() if len(v)>caps[n]};top=sorted(over,key=lambda n:(-over[n],n))[:20]
selected=set().union(*(owners[n] for n in top));assert top==r['details']['top_nodes'] and sorted(selected)==r['details']['selected_nets']
byold={c['connection_id']:c for c in old['connections']};byfull={c['connection_id']:c for c in full['connections']};assert len(byold)==len(new['connections'])==16819
assert {c['connection_id'] for c in new['connections']}==set(byold)
netnodes=defaultdict(set);updated=changed=0
for c in new['connections']:
 prior=byold[c['connection_id']];assert all(c[k]==prior[k] for k in ('net_id','source','sink'))
 target=byfull[c['connection_id']] if c['net_id'] in selected else prior
 assert c['physical_edge_ids']==target['physical_edge_ids']
 updated+=c['net_id'] in selected;changed+=c['physical_edge_ids']!=prior['physical_edge_ids'];netnodes[c['net_id']].update(nodes(c))
occupancy=Counter(n for ns in netnodes.values() for n in ns);assert {str(n):v for n,v in occupancy.items()}==new['node_occupancy']
assert updated==r['details']['recomputed_connections']==2050 and len(selected)==116
out=dict(passed=True,selected_nets=len(selected),updated_connections=updated,actually_changed_paths=changed,untouched_connections=16819-updated,bindings={str(p):sha(p) for p in [Path(__file__),P/'receipt.json',P/'prediction.json',B/'prediction.json',F/'prediction.json',graph]},scope='Independent original XML path continuity and exact selection/full-search equality/untouched paths/net union. Not native joint-tree/nonconfigurable closure or epoch rollback proof.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
