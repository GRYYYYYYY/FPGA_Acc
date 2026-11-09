"""Emit live physical prediction under a current native identity table.

Unique site/class mapping only. Ambiguous pin identities or inconsistent NET
trees fail; caller owns native evidence, input provenance and final FULL/STA.
"""
import json
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha

def serialize(candidate, endpoint_path, identity_path, place_path):
    ep=json.loads(Path(endpoint_path).read_text());graph=Path(ep['inputs']['graph']['path'])
    if sha(graph)!=ep['graph_sha256']:raise ValueError('RR graph identity changed')
    xml=ET.parse(graph).getroot()
    nodes={int(n.get('id')):(n.get('type'),dict(n.find('loc').attrib)) for n in xml.find('rr_nodes')}
    edges=[tuple(int(e.get(k)) for k in ('src_node','sink_node','switch_id')) for e in xml.find('rr_edges')]
    nets={r['name']:r for r in map(json.loads,Path(identity_path).read_text().splitlines())}
    groups=defaultdict(list);bindings={};seen=set()
    queries={q['connection_id']:q for q in ep['connections']}
    records=candidate['records']
    if len(records)!=len(queries):raise ValueError('incomplete candidate cohort')
    for q in records:
        cid=q['connection_id'];name=ep['net_names'][str(q['net_id'])];native=nets[name]
        if cid in seen or any(q[k]!=queries[cid][k] for k in ('net_id','source','sink')):
            raise ValueError('candidate endpoint mismatch')
        seen.add(cid)
        def site(node):
            loc=nodes[node][1];return tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
        source=[p for p in native['pins'] if p['index']==0]
        sinks=[p for p in native['pins'] if p['index']>0 and tuple(p[k] for k in ('x','y','layer','class'))==site(q['sink'])]
        if len(source)!=1 or tuple(source[0][k] for k in ('x','y','layer','class'))!=site(q['source']) or len(sinks)!=1:
            raise ValueError('ambiguous or mismatched native terminal identity')
        bindings[cid]=dict(net=native['net_id'],name=name,pin=sinks[0]['index'])
        groups[native['net_id']].append(q)
    if len({(b['net'],b['pin']) for b in bindings.values()})!=len(bindings):
        raise ValueError('duplicate native terminal binding')
    text=Path(place_path).read_text().splitlines()
    lines=['Placement_File: design.place Placement_ID: SHA256:'+sha(place_path),text[1]+'.','','Routing:','']
    for net,qs in sorted(groups.items()):
        lines.extend([f"Net {net} ({bindings[qs[0]['connection_id']]['name']})",''])
        emitted=set();parents={}
        for q in sorted(qs,key=lambda q:bindings[q['connection_id']]['pin']):
            path=[q['source']];switches=[]
            for eid in q['answer']['physical_edge_ids']:
                u,v,s=edges[eid]
                if u!=path[-1] or v in path:raise ValueError('invalid/cyclic candidate path')
                if v in parents and parents[v]!=(u,s):raise ValueError('inconsistent NET parent')
                parents[v]=(u,s);path.append(v);switches.append(s)
            if path[-1]!=q['sink']:raise ValueError('incomplete candidate path')
            start=0
            if emitted:
                while start+1<len(path) and path[start+1] in emitted:start+=1
                if path[start] not in emitted or any(n in emitted for n in path[start+1:-1]):raise ValueError('invalid NET branch')
            for i in range(start,len(path)):
                node=path[i];kind,loc=nodes[node]
                lo=f"({loc['xlow']},{loc['ylow']},{loc.get('layer','0')})";hi=f"({loc['xhigh']},{loc['yhigh']},{loc.get('layer','0')})"
                coords=lo if lo==hi else lo+' to '+hi
                label='Track' if kind in ('CHANX','CHANY') else 'Class' if kind in ('SOURCE','SINK') else 'Pin'
                switch=switches[i] if i<len(switches) else -1
                line=f"Node:\t{node}\t {kind} {coords} {label}: {loc['ptc']} Switch: {switch}"
                if i==len(path)-1:
                    if kind!='SINK':raise ValueError('invalid sink node')
                    line+=f" Net_pin_index: {bindings[q['connection_id']]['pin']}"
                lines.append(line);emitted.add(node)
        lines.extend(['',''])
    if sha(graph)!=ep['graph_sha256']:raise ValueError('RR graph changed during serialization')
    return '\n'.join(lines)+'\n',bindings
