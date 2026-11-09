"""Evaluator-only archived VPR node unions, bound to placement identity."""
from collections import defaultdict
import re
from pathlib import Path


def node_labels(graph,route,placement_sha256):
    users=defaultdict(set);net=None;nets=set();identity=False
    for line in Path(route).read_text().splitlines():
        if line.startswith('Placement_File:'):
            match=re.search(r'Placement_ID:\s*SHA256:([0-9a-f]{64})',line)
            if match is None or match[1]!=placement_sha256:raise ValueError('route placement identity mismatch')
            identity=True
        match=re.match(r'^\s*Net\s+(\d+)\s+\(',line)
        if match:
            net=int(match[1])
            if net in nets:raise ValueError('duplicate native net header')
            nets.add(net)
        match=re.match(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b',line)
        if match:
            n=int(match[1])
            if net is None or n not in graph.nodes or graph.nodes[n].type!=match[2]:raise ValueError('invalid native node')
            users[n].add(net)
        elif line.lstrip().startswith('Node:'):raise ValueError('unparsed native node')
    if not identity:raise ValueError('missing route placement identity')
    return {str(n):len(v) for n,v in users.items()}
