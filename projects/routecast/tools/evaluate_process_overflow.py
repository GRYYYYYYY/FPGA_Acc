"""Exploratory first-iteration congestion evaluation of frozen full-budget baselines."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
from prediction_metrics import spearman
from rr_graph import read_rr_graph


def evaluate(graph,prediction,labels):
    if prediction['graph_sha256']!=graph.sha256 or labels['graph_sha256']!=graph.sha256:
        raise ValueError('graph mismatch')
    if prediction['connections_completed']!=prediction['connections_requested']:
        raise ValueError('primary process evaluation requires complete cohort')
    channels={nid:node for nid,node in graph.nodes.items() if node.type in {'CHANX','CHANY'} and node.capacity>0}
    first=labels['iterations'][0]
    pred={nid:max(0,prediction['node_occupancy'].get(str(nid),0)-node.capacity) for nid,node in channels.items()}
    truth={nid:first['node_overflow'].get(str(nid),0) for nid in channels}
    p={nid for nid in channels if pred[nid]>0};t={nid for nid in channels if truth[nid]>0}
    overlap=len(p&t);capacities=defaultdict(int);pb=defaultdict(int);tb=defaultdict(int)
    for nid,node in channels.items():
        loc=dict(node.location)
        for x in range(int(loc['xlow']),int(loc['xhigh'])+1):
            for y in range(int(loc['ylow']),int(loc['yhigh'])+1):
                key=(x,y,node.type,node.segment_id);capacities[key]+=node.capacity;pb[key]+=pred[nid];tb[key]+=truth[nid]
    ids=sorted(channels);bins=sorted(capacities)
    return {'mode':prediction['mode'],'resource_universe':len(channels),'truth_positive_nodes':len(t),
            'predicted_positive_nodes':len(p),'true_positive':overlap,
            'precision':None if not p else overlap/len(p),'recall':None if not t else overlap/len(t),
            'resource_overflow_spearman':spearman([pred[n] for n in ids],[truth[n] for n in ids]),
            'spatial_overflow_spearman':spearman([pb[k]/capacities[k] for k in bins],[tb[k]/capacities[k] for k in bins]),
            'label_iteration':first['iteration'],'scope':'exploratory initial-router congestion only; one design/seed, no calibrated routability or feedback claim'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('graph',type=Path);p.add_argument('prediction',type=Path);p.add_argument('labels',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pred=json.loads(a.prediction.read_text())['payload']['prediction'];labels=json.loads(a.labels.read_text())
    result=evaluate(read_rr_graph(a.graph),pred,labels)
    result['input_sha256']={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ('graph','prediction','labels')}
    result['source_sha256']={n:hashlib.sha256(Path(__file__).with_name(n).read_bytes()).hexdigest() for n in ['evaluate_process_overflow.py','prediction_metrics.py','rr_graph.py']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
