"""Route text unique-NET union counts; legality and demand audits are external."""
from collections import Counter
import re

NET = re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)(?:: global net connecting:)?\s*$')
NODE = re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b.*?Switch:\s*(-?\d+)')


def occupancy(route_path):
    result=Counter();seen=set();nodes=set();current=None
    with open(route_path) as stream:
        for line in stream:
            header=NET.match(line)
            if header:
                if current is not None:result.update(nodes)
                current=int(header[1])
                if current in seen:raise ValueError('duplicate NET header')
                seen.add(current);nodes=set()
            elif line.lstrip().startswith('Net '):
                raise ValueError('unrecognized NET header')
            elif line.lstrip().startswith('Node:'):
                node=NODE.match(line)
                if node is None or current is None:raise ValueError('invalid node record')
                nodes.add(int(node[1]))
    if current is not None:result.update(nodes)
    if not seen:raise ValueError('empty NET domain')
    return {str(n):count for n,count in result.items()},len(seen)
