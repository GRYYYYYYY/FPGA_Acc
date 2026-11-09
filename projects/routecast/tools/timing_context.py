"""Observed baseline setup paths mapped to endpoint classes, not full criticality.

Equivalent sink pins remain grouped by (net,SOURCE,SINK); no fabricated mapping
from routed physical pins to individual packed sink connection IDs is supplied.
"""
from collections import defaultdict
import re


def route_pairs(text):
    pairs=defaultdict(set);net=None;paths={};current=None
    for line in text.splitlines():
        match=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
        if match:net=int(match[1]);paths={};current=None
        match=re.match(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b',line)
        if not match:continue
        node=int(match[1]);kind=match[2]
        if net is None:raise ValueError('native node before net')
        if node in paths and kind!='SINK':path=paths[node]
        elif kind=='SOURCE':
            if paths:raise ValueError('multiple roots')
            path=((node,kind),);paths[node]=path
        else:
            if current is None:raise ValueError('native node before root')
            path=paths[current]+((node,kind),);paths[node]=path
        current=node
        if kind=='SINK':
            opins=[n for n,k in path if k=='OPIN'];ipins=[n for n,k in path if k=='IPIN']
            if len(opins)!=1 or len(ipins)!=1:raise ValueError('unsupported native branch pin topology')
            pairs[(opins[0],ipins[0])].add((net,path[0][0],node))
    return dict(pairs)


def observed_context(report,pairs):
    if '# Unit scale: 1e-09 seconds' not in report:raise ValueError('unsupported timing units')
    paths=[];current=None;pending=None;protected=set();seen=set()
    for line in report.splitlines():
        match=re.match(r'^#Path (\d+)\s*$',line)
        if match:
            if pending is not None:raise ValueError('unterminated physical timing segment')
            if current is not None and 'slack_ns' not in current:raise ValueError('missing path slack')
            rank=int(match[1])
            if rank in seen:raise ValueError('duplicate path rank')
            seen.add(rank);current={'rank':rank,'endpoint_groups':[]};paths.append(current)
        kind=re.match(r'^Path Type\s*:\s*(\w+)\s*$',line)
        if kind:
            if current is None or kind[1]!='setup':raise ValueError('expected setup timing context')
            current['path_type']='setup'
        match=re.match(r'^\|\s*\((OPIN|IPIN):(\d+)\b',line)
        if match:
            if current is None:raise ValueError('timing segment before path')
            role=match[1];node=int(match[2])
            if role=='OPIN':
                if pending is not None:raise ValueError('overlapping physical timing segment')
                pending=node
            else:
                if pending is None:raise ValueError('IPIN without OPIN')
                groups=pairs.get((pending,node),set())
                if len(groups)!=1:raise ValueError('missing or ambiguous baseline endpoint join')
                group=next(iter(groups));current['endpoint_groups'].append(group);protected.add(group);pending=None
        match=re.match(r'^slack\s+\([^)]*\)\s+([-+0-9.]+)\s*$',line)
        if match:
            if current is None or pending is not None:raise ValueError('invalid slack location')
            current['slack_ns']=float(match[1])
    if not paths or pending is not None or any('slack_ns' not in p or p.get('path_type')!='setup' for p in paths):raise ValueError('incomplete timing report')
    return {'paths':paths,'observed_endpoint_groups':sorted(protected),'scope':'baseline top reported setup paths only; grouped equivalent endpoints, not complete connection criticality or CPD model'}
