"""Independent original XML paths/topology for two completed frozen snapshots."""
import json,time
from pathlib import Path
from collections import defaultdict,Counter
from array import array
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from prepared_csr import TYPES
from pre_route_endpoints import sha
from streaming_prediction_audit import Nodes,Edges
from physical_prediction_audit import audit
from net_union_topology import diagnose

def run():
    base=Path('experiments/stereo_prospective_validation_2026-10-05')
    out=base/'first_high_fanout_physical_audit';out.mkdir()
    inputs=[base/'completed_high_fanout_snapshots'/f'net_{n}.json' for n in (3103,3482)]
    snapshots=[json.loads(p.read_text()) for p in inputs]
    graph_path=json.loads((base/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host/protocol.json').read_text())['inputs']['graph']['path']
    protocol={'snapshots':{str(p):sha(p) for p in inputs},'graph':{'path':graph_path,'sha256':sha(graph_path)},'source_sha256':sha(__file__),'scope':'two-net original XML path/occupancy/topology audit; no global zero-overuse or native legality'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    rows=[]
    for s in snapshots:
        for r in s['connections']:rows.append({**r,'physical_edge_ids':s['net_result']['result']['paths'][str(r['sink'])],'method':'cached_bound_rc'})
    wanted={eid for r in rows for eid in r['physical_edge_ids']};types=array('B');caps=array('Q');records={};count=0;stack=[];start=time.monotonic()
    for event,e in ET.iterparse(graph_path,events=('start','end')):
        if event=='start':stack.append(e);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            assert int(e.get('id'))==len(types)
            types.append(TYPES[e.get('type')]);caps.append(int(e.get('capacity')))
        elif e.tag=='edge' and parent=='rr_edges':
            if count in wanted:records[count]=SimpleNamespace(source=int(e.get('src_node')),sink=int(e.get('sink_node')),switch_id=int(e.get('switch_id')))
            count+=1
        if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
        stack.pop()
    assert wanted==set(records)
    graph=SimpleNamespace(nodes=Nodes(types,caps),edges=Edges(records,count),sha256=protocol['graph']['sha256'])
    users=defaultdict(set)
    for r in rows:
        users[r['source']].add(r['net_id'])
        for eid in r['physical_edge_ids']:users[records[eid].sink].add(r['net_id'])
    pred={'physical_graph_sha256':graph.sha256,'connections':rows,'node_occupancy':{str(n):len(v) for n,v in users.items()},'methods':dict(Counter(r['method'] for r in rows)),'requested':len(rows),'completed':len(rows)}
    ep={'graph_sha256':graph.sha256,'connections':[r for s in snapshots for r in s['connections']]}
    checked=audit(graph,ep,pred);topology=diagnose(graph,pred)
    assert all(caps[n]>0 for n in users)
    assert sha(graph_path)==graph.sha256 and all(sha(p)==h for p,h in protocol['snapshots'].items())
    receipt={'physical_audit':checked,'topology':topology,'subset_overflow_units':sum(max(0,len(v)-caps[n]) for n,v in users.items()),'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']}
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)

if __name__=='__main__':run()
