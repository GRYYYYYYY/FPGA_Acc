"""Independent artifact audit: replay physical arcs and rebuild per-net occupancy."""
from collections import Counter, defaultdict
import argparse
import hashlib
import json
from pathlib import Path
from rr_graph import read_rr_graph
from template_sketch import quotient
from template_connectivity import refine


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def verify(out):
    protocol=json.loads((out/'protocol.json').read_text());receipt=json.loads((out/'receipt.json').read_text())
    if receipt['protocol_sha256']!=sha(out/'protocol.json'):raise ValueError('protocol receipt mismatch')
    for n,digest in protocol['source_sha256'].items():
        if sha(out/'source'/n)!=digest:raise ValueError('frozen source changed')
        if sha(Path(__file__).with_name(n))!=digest:raise ValueError('use matching source snapshot for replay')
    for entry in protocol['inputs'].values():
        if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
    graph=read_rr_graph(protocol['inputs']['graph']['path'])
    endpoints=json.loads(Path(protocol['inputs']['endpoints']['path']).read_text())
    fields=('connection_id','net_id','source','sink')
    expected=Counter(tuple(row[k] for k in fields) for row in endpoints['connections'])
    coarse,initial,_=quotient(graph,True);audits=[]
    for rounds in protocol['refinement_rounds']:
        name='fixed' if rounds is None else str(rounds);target=out/f'refinement_{name}.json'
        if sha(target)!=receipt['artifact_sha256'][target.name]:raise ValueError('prediction artifact changed')
        record=json.loads(target.read_text());pooled,mapping,members,_,fixed=refine(graph,coarse,initial,rounds)
        if pooled.sha256!=record['quotient_graph_sha256']:raise ValueError('quotient identity mismatch')
        if Counter(tuple(row[k] for k in fields) for row in record['connections'])!=expected:raise ValueError('cohort changed')
        nets=defaultdict(set);verified=0
        for row in record['connections']:
            physical=row['physical_edge_ids']
            if physical is None:continue
            if len(physical)!=len(row['quotient_edge_ids']):raise ValueError('path length mismatch')
            current=row['source'];used={current}
            for eid,qid in zip(physical,row['quotient_edge_ids']):
                edge=graph.edges[eid];qe=pooled.edges[qid]
                if edge.source!=current or edge.sink in used or not graph.nodes[edge.sink].capacity:
                    raise ValueError('physical path discontinuity/cycle/zero capacity')
                if (mapping[edge.source],mapping[edge.sink],edge.switch_id)!=(qe.source,qe.sink,qe.switch_id):
                    raise ValueError('physical switch arc does not project to chosen template edge')
                current=edge.sink;used.add(current)
            if current!=row['sink']:raise ValueError('wrong physical sink')
            nets[row['net_id']].update(used);verified+=1
        demand=Counter(nid for used in nets.values() for nid in used)
        if {str(n):v for n,v in demand.items()}!=record['node_occupancy']:raise ValueError('independent per-net union mismatch')
        if verified!=record['lifted_connections']:raise ValueError('lift count mismatch')
        # Check outgoing signatures directly, without using stable() helper.
        exits={nid:set() for nid in graph.nodes}
        for edge in graph.edges:
            if graph.nodes[edge.source].capacity and graph.nodes[edge.sink].capacity:
                exits[edge.source].add((edge.switch_id,mapping[edge.sink]))
        independently_stable=all(all((bool(graph.nodes[n].capacity),exits[n])==
                                    (bool(graph.nodes[ids[0]].capacity),exits[ids[0]]) for n in ids) for ids in members.values())
        if independently_stable!=fixed:raise ValueError('stable-signature proof mismatch')
        if fixed and verified!=len(endpoints['connections']):raise ValueError('stable partition missing physical path')
        channel_cells=[ids for ids in members.values() if graph.nodes[ids[0]].type in {'CHANX','CHANY'}]
        audits.append({'rounds':rounds,'physical_paths_verified':verified,'requested':len(endpoints['connections']),
                       'stable_signatures_independently_verified':independently_stable,
                       'channel_cells':len(channel_cells),'merged_channel_cells':sum(len(ids)>1 for ids in channel_cells),
                       'net_occupancy_rebuild_matches':True})
    return {'protocol_sha256':receipt['protocol_sha256'],'audit':audits,'all_checked_invariants_passed':True}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output_dir',type=Path);a=p.parse_args();result=verify(a.output_dir)
    result['verifier_sha256']=sha(Path(__file__))
    (a.output_dir/'independent_audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
