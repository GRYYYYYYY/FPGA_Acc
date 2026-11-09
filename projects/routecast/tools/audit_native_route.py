"""Replay archived VPR text route branches into the independent node ledger.

Checks printed arcs/switches and net-union occupancy. Not a native VPR legality
check: pin mapping, route-tree topology and non-configurable closure remain external.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from connection_golden import Result
from rr_graph import read_rr_graph
from rr_occupancy import Occupancy

NET=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)\s*$')
NODE=re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b.*?Switch:\s*(-?\d+)')


def audit(graph_path,route_path):
    graph=read_rr_graph(graph_path); ledger=Occupancy(graph)
    arcs=defaultdict(list)
    for eid,edge in enumerate(graph.edges): arcs[(edge.source,edge.sink,edge.switch_id)].append(eid)
    net=None; paths={}; current=None; outgoing=None; expected={}; records=[]; printed=0
    for line_no,line in enumerate(Path(route_path).read_text().splitlines(),1):
        match=NET.match(line)
        if match:
            net=int(match[1]); paths={}; current=None; outgoing=None
            if net in expected: raise ValueError('duplicate net header')
            expected[net]=set(); continue
        match=NODE.match(line)
        if not match:
            if line.lstrip().startswith('Node:'): raise ValueError(f'unparsed node at line {line_no}')
            continue
        if net is None: raise ValueError('node before net')
        nid=int(match[1]); kind=match[2]; switch=int(match[3]); printed+=1
        if nid not in graph.nodes or graph.nodes[nid].type!=kind: raise ValueError('node/type mismatch')
        expected[net].add(nid)
        if nid in paths and kind!='SINK':
            path=paths[nid]
        elif kind=='SOURCE':
            if paths: raise ValueError('multiple source roots')
            path=(); paths[nid]=path
        else:
            if current is None: raise ValueError('node before source')
            candidates=arcs[(current,nid,outgoing)]
            if not candidates: raise ValueError(f'printed arc/switch absent at line {line_no}')
            path=paths[current]+(min(candidates),); paths[nid]=path
        current=nid; outgoing=switch
        if kind=='SINK':
            source=graph.edges[path[0]].source if path else nid
            cid=len(records)
            result=ledger.update(cid,1,net,source,nid,path)
            if result!=Result.COMMITTED: raise ValueError(f'ledger rejected connection {cid}: {result}')
            records.append({'connection_id':cid,'net_id':net,'source':source,'sink':nid,'edge_ids':path})
    totals=Counter(nid for used in expected.values() for nid in used)
    independent={nid:totals[nid] for nid in graph.nodes}
    if ledger.occupancy!=independent: raise AssertionError('native printed-node union mismatch')
    if ledger.occupancy!=ledger.rebuild(): raise AssertionError('rebuild mismatch')
    baseline=ledger.occupancy
    for record in records:
        cid=record['connection_id']
        assert ledger.update(cid,2,remove=True)==Result.COMMITTED
        assert ledger.occupancy==ledger.rebuild()
        assert ledger.update(cid,1,record['net_id'],record['source'],record['sink'],record['edge_ids'])==Result.STALE
        assert ledger.update(cid,3,record['net_id'],record['source'],record['sink'],record['edge_ids'])==Result.COMMITTED
        assert ledger.occupancy==baseline
    return {'schema':'ROUTECAST_NATIVE_ROUTE_OCCUPANCY_AUDIT_V1',
            'graph_path':str(Path(graph_path).resolve()),'graph_sha256':graph.sha256,
            'route_path':str(Path(route_path).resolve()),'route_sha256':hashlib.sha256(Path(route_path).read_bytes()).hexdigest(),
            'connections':records,'routed_nets':sum(bool(x) for x in expected.values()),'printed_nodes':printed,
            'occupied_nodes':sum(value>0 for value in baseline.values()),
            'shared_node_occurrences_saved':sum(1+len(r['edge_ids']) for r in records)-sum(map(len,expected.values())),
            'overflow_nodes':ledger.overflow(),'all_union_and_remove_restore_checks_passed':True,
            'scope':'Archived route XML arc/switch integrity and unique-net node accounting; not new routing QoR or native legality'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('graph',type=Path); parser.add_argument('route',type=Path)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    result=audit(args.graph,args.route); args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('routed_nets','printed_nodes','occupied_nodes','shared_node_occurrences_saved')}))
