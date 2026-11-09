"""Canonical pin labels from post-route identity; physical trace stays exact."""
import re
from audit_native_route import NET,NODE
from rooted_native_sink_pin_v1 import resolve

def physical_sequences(lines):
    sequences={};name=None
    for line in lines:
        net=NET.match(line)
        if net:
            name=net[2]
            if name in sequences:raise ValueError('duplicate NET section')
            sequences[name]=[]
        node=NODE.match(line)
        if node:
            if name is None:raise ValueError('node outside NET')
            sequences[name].append((int(node[1]),node[2],int(node[3])))
    return sequences

def render(lines,native,nodes,grid,pin_classes,placement_sha):
    original=physical_sequences(lines);head=[];sections={};record=None;previous=None;pins=0
    for line in lines:
        net=NET.match(line)
        if net:
            record=native[net[2]];nid=record['net_id']
            if nid in sections:raise ValueError('duplicate canonical NET ID')
            sections[nid]=[re.sub(r'^(\s*Net\s+)\d+',lambda m:m[1]+str(nid),line)]
            previous=None;continue
        if record is None:head.append(line);continue
        node=NODE.match(line)
        if node:
            nid=int(node[1]);kind=node[2]
            if nodes[nid]['type']!=kind:raise ValueError('trace node type mismatch')
            if kind=='SINK':
                if previous is None:raise ValueError('SINK without IPIN')
                index=resolve(record,nodes[previous],nodes[nid],grid,pin_classes)
                line,count=re.subn(r'Net_pin_index:\s*-?\d+',f'Net_pin_index: {index}',line)
                if count!=1:raise ValueError('missing/duplicate sink pin index')
                pins+=1
            previous=nid
        sections[record['net_id']].append(line)
    if not head or not head[0].startswith('Placement_File:'):raise ValueError('missing placement header')
    head[0]='Placement_File: design.place Placement_ID: SHA256:'+placement_sha
    result=head[:]
    for nid in sorted(sections):result.extend(sections[nid])
    if physical_sequences(result)!=original:raise ValueError('physical trace changed')
    return result,pins
