"""Independent raw-edge replay and unique-net occupancy audit of hybrid artifacts."""
import json
import hashlib
from collections import defaultdict
from pathlib import Path
from rr_graph import read_rr_graph

root=Path('experiments/lazy_repair_serialization_fix_2026-10-04')
p=json.loads((root/'protocol.json').read_text())
g=read_rr_graph(p['inputs']['graph']['path'])
reports=[]
for variant in p['candidates']:
    candidate=json.loads(Path(p['candidates'][variant]['path']).read_text())
    originals={r['connection_id']:r for r in candidate['connections']}
    for target in (Path(p['eager_artifacts'][variant]['path']),root/f'lazy_{variant}.json'):
        data=json.loads(target.read_text());users=defaultdict(set)
        for r in data['connections']:
            node=r['source'];visited={node}
            assert g.nodes[node].type=='SOURCE'
            for eid in r['physical_edge_ids']:
                edge=g.edges[eid];assert edge.source==node
                node=edge.sink;assert node not in visited;visited.add(node)
            assert node==r['sink'] and g.nodes[node].type=='SINK'
            if r['method']=='lifted':assert r['physical_edge_ids']==originals[r['connection_id']]['physical_edge_ids']
            for n in visited:users[n].add(r['net_id'])
        assert {str(n):len(v) for n,v in users.items()}==data['node_occupancy']
        reports.append({'artifact':str(target),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'paths':len(data['connections']),'raw_arc_replay_and_net_union_passed':True})
(root/'independent_audit.json').write_text(json.dumps(reports,indent=2)+'\n')
print('Independent raw-edge replay and net union passed for',len(reports),'artifacts')
