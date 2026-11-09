"""Reproduce full-graph reachability for failed native VPR connection diagnostics."""
import argparse,hashlib,json,re
from collections import Counter,deque
from pathlib import Path
import xml.etree.ElementTree as ET
p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',type=Path);p.add_argument('output',type=Path);a=p.parse_args();case=a.case.resolve()
log=(case/'vpr.log').read_text();pairs=list(dict.fromkeys(tuple(map(int,m)) for m in re.findall(r'Cannot route from .*?\(RR node: (\d+).*?to .*?\(RR node: (\d+)',log)));assert pairs
layers=[];kinds=[];adj=[];cross=Counter();cross_types=Counter();edges=0
for _,e in ET.iterparse(case/'rr_graph.xml',events=['end']):
 if e.tag=='node':
  assert int(e.attrib['id'])==len(layers);loc=e.find('loc');assert loc is not None and 'layer' in loc.attrib
  layers.append(int(loc.attrib['layer']));kinds.append(e.attrib['type']);adj.append([]);e.clear()
 elif e.tag=='edge':
  u,v=(int(e.attrib[k]) for k in ['src_node','sink_node']);assert max(u,v)<len(adj);adj[u].append(v);edges+=1
  if layers[u]!=layers[v]:cross[(layers[u],layers[v])]+=1;cross_types[(kinds[u],kinds[v])]+=1
  e.clear()
results=[]
for source,target in pairs:
 assert max(source,target)<len(adj)
 seen={source};queue=deque([source])
 while queue:
  u=queue.popleft()
  for v in adj[u]:
   if v not in seen:seen.add(v);queue.append(v)
 results.append(dict(source=source,target=target,source_layer=layers[source],target_layer=layers[target],target_reachable=target in seen,reachable_nodes=len(seen),reachable_nodes_per_layer=dict(Counter(layers[i] for i in seen))))
files=[case/'vpr.log',case/'rr_graph.xml',case/'architecture.xml',case/'run.json',Path(__file__).resolve()]
r=dict(status='failed_native_connections_unreachable_in_full_rr_graph' if all(not r['target_reachable'] for r in results) else 'failed_native_connection_has_structural_path_requires_other_diagnosis',rr_nodes=len(layers),rr_edges=edges,directed_cross_layer_edges={str(k):v for k,v in cross.items()},cross_edge_types={str(k):v for k,v in cross_types.items()},failures=results,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},scope='Unbounded BFS over every exported directed edge,withoutcapacity,cost,bboxorsearchlimit. Establishes reachability only;doesnotassign algorithmperformance,commercialphysicalmeaningorqualityacceptance.',board_result=False,research_complete=False)
with a.output.open('x') as out:json.dump(r,out,indent=2);out.write('\n')
print(json.dumps(dict(status=r['status'],failures=results)))
