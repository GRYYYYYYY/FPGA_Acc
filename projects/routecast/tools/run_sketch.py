"""Predictor CLI: deliberately has no argument for final route labels."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import time
from connection_golden import Result, UINT64_MAX, integer
from rr_graph import read_rr_graph
from rr_occupancy import Occupancy
from semantic_sketch import Sketch


def predict(graph,endpoints,mode,budget):
    if endpoints.get('schema')!='ROUTECAST_ENDPOINTS_V1' or endpoints.get('graph_sha256')!=graph.sha256:
        raise ValueError('endpoint schema or graph identity mismatch')
    groups=defaultdict(list); seen=set()
    for row in endpoints['connections']:
        if set(row)!={'connection_id','net_id','source','sink'}: raise ValueError('extra fields, possibly labels')
        if any(not integer(row[k],0,UINT64_MAX) for k in row): raise ValueError('invalid endpoint fields')
        if row['connection_id'] in seen: raise ValueError('duplicate connection ID')
        seen.add(row['connection_id']); groups[row['source']].append(row)
    sketch=Sketch(graph,mode,budget); ledger=Occupancy(graph); failures=[]; traces=[]
    started=time.monotonic()
    for source,rows in sorted(groups.items()):
        result=sketch.search(source,{r['sink'] for r in rows})
        for row in sorted(rows,key=lambda r:r['connection_id']):
            path=result.paths.get(row['sink'])
            if path is None:
                failures.append({'connection_id':row['connection_id'],
                                 'reason':'node_budget' if result.budget_exhausted else 'unreachable'})
            elif ledger.update(row['connection_id'],1,row['net_id'],source,row['sink'],path)!=Result.COMMITTED:
                raise ValueError('path rejected by independent ledger')
        traces.append({'source':source,'settled_nodes':result.settled_nodes,'edge_visits':result.edge_visits,
                       'budget_exhausted':result.budget_exhausted})
    return {'schema':'ROUTECAST_SKETCH_PREDICTION_V1','graph_sha256':graph.sha256,'mode':mode,'node_budget':budget,
            'connections_requested':len(seen),'connections_completed':len(seen)-len(failures),'failures':failures,
            'search_and_commit_wall_s':time.monotonic()-started,'search_traces':traces,
            'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},
            'overflow_nodes':{str(n):v for n,v in ledger.overflow().items()},
            'scope':'frozen-cost development baseline; CPU wall time is not hardware evidence'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('graph',type=Path);p.add_argument('endpoints',type=Path)
    p.add_argument('--mode',choices=['rr_hop','rr_length_switch'],required=True)
    p.add_argument('--node-budget',type=int,default=4096);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    graph=read_rr_graph(a.graph); inputs=a.endpoints.read_bytes(); result=predict(graph,json.loads(inputs),a.mode,a.node_budget)
    result['endpoints_sha256']=hashlib.sha256(inputs).hexdigest()
    result['source_sha256']={name:hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                             for name in ['run_sketch.py','semantic_sketch.py','rr_graph.py','rr_occupancy.py','connection_golden.py']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['mode','connections_completed','connections_requested','search_and_commit_wall_s']}))
