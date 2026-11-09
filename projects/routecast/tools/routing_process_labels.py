"""Audit printed unique-net occupancy against native VPR iteration overuse."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from rr_graph import read_rr_graph

NET=re.compile(r'^\s*Net\s+(\d+)\s+\(.*\)(.*)$')
NODE=re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|IPIN|OPIN|CHANX|CHANY)\b')
TABLE=re.compile(r'^\s*(\d+)\s+[0-9.eE+-]+\s+[0-9.eE+-]+\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+(\d+)\s+\(')


def native_table(text):
    rows={}
    for line in text.splitlines():
        match=TABLE.match(line)
        if match:
            iteration,nets,connections,overuse=map(int,match.groups())
            if iteration in rows:raise ValueError('duplicate iteration row')
            rows[iteration]={'rerouted_nets':nets,'rerouted_connections':connections,'overused_nodes':overuse}
    if not rows:raise ValueError('no VPR iteration table')
    return rows


def node_occupancy(text,graph):
    nets=defaultdict(set);current=None;global_net=False;seen=set()
    for line in text.splitlines():
        match=NET.match(line)
        if match:
            current=int(match[1]);global_net='global net' in match[2]
            if current in seen:raise ValueError('duplicate net header')
            seen.add(current);continue
        match=NODE.match(line)
        if match:
            if current is None or global_net:raise ValueError('RR nodes outside nonglobal net')
            nid=int(match[1])
            if nid not in graph.nodes or graph.nodes[nid].type!=match[2]:raise ValueError('node/type mismatch')
            nets[current].add(nid)
        elif line.lstrip().startswith('Node:'):raise ValueError('unsupported printed node')
    return Counter(nid for used in nets.values() for nid in used)


def build(graph,iteration_files,log):
    table=native_table(log)
    if 'Total local nets with reserved CLB opins: 0' not in log:
        raise ValueError('local OPIN reservations require additional resource labels')
    if 'Completed routing consistency check successfully.' not in log or 'VPR succeeded' not in log:
        raise ValueError('native terminal success/consistency evidence missing')
    recurrence=Counter();peak=Counter();rows=[]
    files=sorted(iteration_files,key=lambda p:int(p.stem.split('_')[-1]))
    for path in files:
        iteration=int(path.stem.split('_')[-1]);occupancy=node_occupancy(path.read_text(),graph)
        overflow={nid:value-graph.nodes[nid].capacity for nid,value in occupancy.items() if value>graph.nodes[nid].capacity}
        if iteration not in table or len(overflow)!=table[iteration]['overused_nodes']:
            raise ValueError(f'printed occupancy does not reproduce VPR overuse at {iteration}')
        for nid,value in overflow.items():recurrence[nid]+=1;peak[nid]=max(peak[nid],value)
        rows.append({'iteration':iteration,**table[iteration],'route_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                     'node_occupancy':{str(n):v for n,v in occupancy.items()},
                     'node_overflow':{str(n):v for n,v in overflow.items()}})
    if {r['iteration'] for r in rows}!=set(table):raise ValueError('missing iteration routes')
    if not rows or rows[0]['iteration']!=1 or rows[-1]['overused_nodes']!=0:raise ValueError('capture lacks initial/final trajectory')
    return {'schema':'ROUTECAST_ROUTING_PROCESS_LABELS_V1','graph_sha256':graph.sha256,'iterations':rows,
            'overflow_recurrence':{str(n):v for n,v in recurrence.items()},'peak_node_overflow':{str(n):v for n,v in peak.items()},
            'all_native_overuse_counts_reproduced':True,'scope':'one native run; resource occupancy union only, not a general route legality checker'}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('graph',type=Path);p.add_argument('work',type=Path);p.add_argument('log',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();g=read_rr_graph(a.graph)
    result=build(g,list(a.work.glob('iteration_*.route')),a.log.read_text());result['log_sha256']=hashlib.sha256(a.log.read_bytes()).hexdigest()
    result['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'iterations':len(result['iterations']),'overuse':[r['overused_nodes'] for r in result['iterations']]}))
