"""Independent endpoint/physical-arc/net-union audit; no predictor invocation."""
from collections import defaultdict,Counter
import argparse,hashlib,json
from pathlib import Path
from rr_graph import read_rr_graph


def audit(graph,endpoints,prediction,candidate=None):
    fields=('connection_id','net_id','source','sink')
    expected={r['connection_id']:tuple(r[k] for k in fields) for r in endpoints['connections']}
    if len(expected)!=len(endpoints['connections']):raise ValueError('duplicate endpoint identity')
    if prediction['physical_graph_sha256']!=graph.sha256 or endpoints['graph_sha256']!=graph.sha256:raise ValueError('graph identity mismatch')
    originals={r['connection_id']:r for r in candidate['connections']} if candidate else None
    seen=set();users=defaultdict(set);methods=Counter();touches=0
    for r in prediction['connections']:
        cid=r['connection_id']
        if cid in seen or expected.get(cid)!=tuple(r[k] for k in fields):raise ValueError('endpoint cohort mismatch')
        seen.add(cid);methods[r['method']]+=1;path=r['physical_edge_ids']
        if path is None:
            if r['method']!='failed':raise ValueError('missing path marked completed')
            continue
        if r['method']=='failed':raise ValueError('failed path has physical witness')
        if originals is not None:
            original=originals[cid]['physical_edge_ids']
            if original is not None and (r['method']!='lifted' or path!=original):raise ValueError('lifted path mutated')
            if original is None and r['method']=='lifted':raise ValueError('failed lift marked lifted')
        n=r['source'];nodes={n}
        if graph.nodes[n].type!='SOURCE':raise ValueError('invalid source type')
        for eid in path:
            if type(eid) is not int or eid<0 or eid>=len(graph.edges):raise ValueError('invalid edge identity')
            edge=graph.edges[eid]
            if edge.source!=n:raise ValueError('discontinuous physical path')
            n=edge.sink
            if n in nodes:raise ValueError('cyclic physical path')
            nodes.add(n)
        if n!=r['sink'] or graph.nodes[n].type!='SINK':raise ValueError('invalid sink')
        touches+=len(nodes)
        for n in nodes:users[n].add(r['net_id'])
    if seen!=set(expected):raise ValueError('incomplete cohort')
    occupancy={str(n):len(v) for n,v in users.items()}
    if occupancy!=prediction['node_occupancy']:raise ValueError('unique-net occupancy mismatch')
    if dict(methods)!=prediction['methods']:raise ValueError('method counters inconsistent')
    complete=len(seen)-methods['failed']
    if prediction['completed']!=complete or prediction['requested']!=len(seen):raise ValueError('completion counters inconsistent')
    return {'requested':len(seen),'completed':complete,'methods':dict(methods),'occupied_nodes':len(users),'connection_node_touches':touches,'net_node_touches':sum(map(len,users.values())),'all_physical_and_union_checks_passed':True,'scope':'individual arc paths and unique-net accounting, not joint route-tree legality'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',type=Path);a=p.parse_args();root=a.experiment
    proto=json.loads((root/'protocol.json').read_text());receipt=json.loads((root/'receipt.json').read_text())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    if receipt['protocol_sha256']!=sha(root/'protocol.json'):raise ValueError('protocol changed')
    for entry in proto['inputs'].values():
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    for n,h in receipt['artifacts'].items():
        if sha(root/n)!=h:raise ValueError('artifact changed')
    g=read_rr_graph(proto['inputs']['graph']['path']);e=json.loads(Path(proto['inputs']['endpoints']['path']).read_text());reports={}
    for rounds in proto['variants']:
        n='fixed' if rounds is None else str(rounds)
        reports[n]=audit(g,e,json.loads((root/f'hybrid_{n}.json').read_text()),json.loads((root/f'candidate_{n}.json').read_text()))
    (root/'independent_path_audit.json').write_text(json.dumps({'auditor_sha256':sha(__file__),'reports':reports},indent=2)+'\n')
    print(json.dumps(reports))
