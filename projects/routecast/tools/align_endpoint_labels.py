"""Evaluator-side label join; never an input to endpoint extraction/prediction."""
from collections import defaultdict, deque
import argparse
import hashlib
import json
from pathlib import Path


def align(endpoints,labels):
    if endpoints['graph_sha256']!=labels['graph_sha256']:raise ValueError('graph identity mismatch')
    buckets=defaultdict(deque)
    for row in labels['connections']:
        buckets[(row['net_id'],row['source'],row['sink'])].append(row)
    result=dict(labels);result['connections']=[];ids=set()
    for row in endpoints['connections']:
        cid=row['connection_id']
        if cid in ids:raise ValueError('duplicate endpoint connection ID')
        ids.add(cid);key=(row['net_id'],row['source'],row['sink'])
        if not buckets[key]:raise ValueError('endpoint missing in label cohort')
        label=dict(buckets[key].popleft());label['connection_id']=cid
        result['connections'].append(label)
    if any(buckets.values()):raise ValueError('extra labels outside endpoint cohort')
    result['alignment']='exact multiset join on (net_id,source,sink), label connection IDs reassigned to pre-route IDs'
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('endpoints',type=Path);p.add_argument('labels',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=align(json.loads(a.endpoints.read_text()),json.loads(a.labels.read_text()))
    result['alignment_input_sha256']={k:hashlib.sha256(getattr(a,k).read_bytes()).hexdigest() for k in ('endpoints','labels')}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
