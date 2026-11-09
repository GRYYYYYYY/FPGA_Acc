"""Label-consuming evaluator kept separate from graph/endpoint-only predictor."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from prediction_metrics import compare
from rr_graph import read_rr_graph


def evaluate(graph,prediction,labels,endpoints):
    if prediction['graph_sha256']!=graph.sha256 or labels['graph_sha256']!=graph.sha256:
        raise ValueError('graph identity mismatch')
    fields=('connection_id','net_id','source','sink')
    if [tuple(r[k] for k in fields) for r in labels['connections']]!=[tuple(r[k] for k in fields) for r in endpoints['connections']]:
        raise ValueError('endpoint cohort differs from label cohort')
    true_nets=defaultdict(set)
    for row in labels['connections']:
        current=row['source']; used={current}
        for eid in row['edge_ids']:
            edge=graph.edges[eid]
            if edge.source!=current: raise ValueError('discontinuous label path')
            current=edge.sink; used.add(current)
        if current!=row['sink']: raise ValueError('wrong label sink')
        for nid in used: true_nets[nid].add(row['net_id'])
    channels={nid:node for nid,node in graph.nodes.items() if node.type in {'CHANX','CHANY'} and node.capacity>0}
    predicted={nid:prediction['node_occupancy'].get(str(nid),0)/node.capacity for nid,node in channels.items()}
    truth={nid:len(true_nets[nid])/node.capacity for nid,node in channels.items()}
    # Spatial channel bins use every physical tile covered by a channel, not just
    # its low-coordinate anchor. Segment/type identity is retained.
    capacities=defaultdict(int); pred_bins=defaultdict(int); true_bins=defaultdict(int)
    for nid,node in channels.items():
        loc=dict(node.location)
        for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
            for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
                key=f'{x},{y},{node.type},{node.segment_id}'
                capacities[key]+=node.capacity
                pred_bins[key]+=prediction['node_occupancy'].get(str(nid),0)
                true_bins[key]+=len(true_nets[nid])
    return {'resource_utilization':compare(predicted,truth,100),
            'spatial_segment_utilization':compare({k:pred_bins[k]/v for k,v in capacities.items()},
                                                 {k:true_bins[k]/v for k,v in capacities.items()},20),
            'connections_requested':prediction['connections_requested'],
            'connections_completed':prediction['connections_completed'],
            'failures_included_as_zero_occupancy':True,'mode':prediction['mode'],
            'predicted_overflow_nodes':len(prediction['overflow_nodes']),
            'label_scope':'final-route occupancy; not overflow trajectory, RRR or routability labels',
            'claim_boundary':'single architecture development pilot; post-route-derived endpoints; no feedback or speedup claim'}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ['graph','prediction','labels','endpoints']:p.add_argument(name,type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pred=json.loads(a.prediction.read_text()); end=json.loads(a.endpoints.read_text())
    if pred['endpoints_sha256']!=hashlib.sha256(a.endpoints.read_bytes()).hexdigest(): raise ValueError('endpoint identity mismatch')
    result=evaluate(read_rr_graph(a.graph),pred,json.loads(a.labels.read_text()),end)
    result['input_sha256']={name:hashlib.sha256(getattr(a,name).read_bytes()).hexdigest() for name in ['graph','prediction','labels','endpoints']}
    result['source_sha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest() for name in ['evaluate_sketch.py','prediction_metrics.py','rr_graph.py']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['mode','resource_utilization','spatial_segment_utilization']}))
