"""Direct originalXML capacity reachability proof for frozen incremental failure."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];parent=root/'experiments/ex5p_swap_incremental_2026-10-06';r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');out=root/'experiments/ex5p_swap_capacity_diagnosis_2026-10-06';out.mkdir();ep=root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json';e=json.loads(ep.read_text());g=Path(e['inputs']['graph']['path']);assert sha(g)==r['graph_sha256'];q=r['failure']['query'];(out/'protocol.json').write_text(json.dumps({'parent_sha256':sha(parent/'receipt.json'),'endpoint_sha256':sha(ep),'graph_sha256':sha(g),'query':q,'policy':'Independent originalXML perNET union reconstruction and residual capacity traversal; no delay model or native reference paths read.'},indent=2)+'\n');xml=ET.parse(g).getroot();caps={int(n.get('id')):int(n.get('capacity')) for n in xml.find('rr_nodes')};edges=list(xml.find('rr_edges'));adj=defaultdict(list);unions=defaultdict(set)
for edge in edges:adj[int(edge.get('src_node'))].append(int(edge.get('sink_node')))
for rec in r['records']:
 node=rec['source'];unions[rec['net_id']].add(node)
 for eid in rec['answer']['physical_edge_ids']:
  edge=edges[eid];assert int(edge.get('src_node'))==node;node=int(edge.get('sink_node'));unions[rec['net_id']].add(node)
 assert node==rec['sink']
ledger=Counter(n for ns in unions.values() for n in ns);assert dict(ledger)=={int(n):c for n,c in r['ledger'].items()};own=unions[q['net_id']];other={n:c-int(n in own) for n,c in ledger.items()};reachable=set();stack=[]
if other.get(q['source'],0)<caps[q['source']]:reachable.add(q['source']);stack.append(q['source'])
while stack:
 for n in adj[stack.pop()]:
  if n not in reachable and other.get(n,0)<caps[n]:reachable.add(n);stack.append(n)
frontier=sorted({n for u in reachable for n in adj[u] if n not in reachable}) if reachable else [q['source']];assert all(other.get(n,0)>=caps[n] for n in frontier);owners={n:sorted(net for net,ns in unions.items() if net!=q['net_id'] and n in ns) for n in frontier};result={'residual_capacity_disconnected':q['sink'] not in reachable,'reachable_nodes':sorted(reachable),'blocked_frontier_nodes':frontier,'frontier_owners':owners,'other_demand':{n:c for n,c in other.items() if c},'parent_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Frozen residual capacity reachability, not global routing infeasibility, timing optimality or changed placement native quality.'};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('disconnected',result['residual_capacity_disconnected'],'reachable',len(reachable),'frontier',len(frontier),'owners',sorted({net for ns in owners.values() for net in ns}))
