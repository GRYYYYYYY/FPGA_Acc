"""Emit live physical prediction under a current native identity table.

Complete selected NETs only; all omitted NETs remain native rerouting work. Unique site/class mapping only. Ambiguous pin identities or inconsistent NET
trees fail; caller owns native evidence, input provenance and final FULL/STA.
"""
import json
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha

def _serialize(candidate, endpoint_path, identity_path, place_path, inventory, cache):
    ep=json.loads(Path(endpoint_path).read_text());graph=Path(ep['inputs']['graph']['path'])
    if sha(graph)!=ep['graph_sha256']:raise ValueError('RR graph identity changed')
    inventory.validate(graph,ep['graph_sha256']);nodes=inventory.nodes;edges=inventory.edges
    nets={r['name']:r for r in map(json.loads,Path(identity_path).read_text().splitlines())}
    pin_indexes={}
    for name,native in nets.items():
        sources=[];sinks=defaultdict(list)
        for pin in native['pins']:
            if pin['index']==0:sources.append(pin)
            elif pin['index']>0:
                sinks[tuple(pin[k] for k in ('x','y','layer','class'))].append(pin)
        pin_indexes[name]=(sources,sinks)
    groups=defaultdict(list);bindings={};seen=set()
    queries={q['connection_id']:q for q in ep['connections']}
    records=candidate['records']
    selected_nets={r['net_id'] for r in records}
    expected={q['connection_id'] for q in ep['connections'] if q['net_id'] in selected_nets}
    if len(records)!=len(expected) or {r['connection_id'] for r in records}!=expected:raise ValueError('incomplete retained NET: no sink omission allowed')
    for q in records:
        cid=q['connection_id'];name=ep['net_names'][str(q['net_id'])];native=nets[name]
        if cid in seen or any(q[k]!=queries[cid][k] for k in ('net_id','source','sink')):
            raise ValueError('candidate endpoint mismatch')
        seen.add(cid)
        def site(node):
            loc=nodes[node][1];return tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
        source,sink_index=pin_indexes[name]
        sinks=sink_index.get(site(q['sink']),[])
        if len(source)!=1 or tuple(source[0][k] for k in ('x','y','layer','class'))!=site(q['source']) or len(sinks)!=1:
            raise ValueError('ambiguous or mismatched native terminal identity')
        bindings[cid]=dict(net=native['net_id'],name=name,pin=sinks[0]['index'])
        groups[native['net_id']].append(q)
    if len({(b['net'],b['pin']) for b in bindings.values()})!=len(bindings):
        raise ValueError('duplicate native terminal binding')
    text=Path(place_path).read_text().splitlines()
    lines=['Placement_File: design.place Placement_ID: SHA256:'+sha(place_path),text[1]+'.','','Routing:','']
    for net,qs in sorted(groups.items()):
        # Complete immutable output dependencies; current pin/endpoint checks above
        # and whole-graph checks are executed even on cache hits.
        key=(str(graph.absolute()),ep['graph_sha256'],net,
             tuple((q['connection_id'],q['source'],q['sink'],
                    bindings[q['connection_id']]['name'],bindings[q['connection_id']]['pin'],
                    tuple(q['answer']['physical_edge_ids']))
                   for q in sorted(qs,key=lambda q:q['connection_id'])))
        saved=cache.get(key)
        if saved is not None:
            lines.extend(saved);continue
        fragment_start=len(lines)
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
        cache.stage(key,tuple(lines[fragment_start:]))
    if sha(graph)!=ep['graph_sha256']:raise ValueError('RR graph changed during serialization')
    return '\n'.join(lines)+'\n',bindings


from collections import OrderedDict
class Session:
    """Serial bounded text-payload cache, not model/placement transaction state.

    Invalid requests never publish newly rendered fragments. Entry keys and text
    are immutable; the byte budget covers encoded fragment text, not Python RSS.
    Initialization, key scans, guards, complete output and writes remain charged.
    """
    def __init__(self,max_text_bytes=64*1024*1024,max_entries=100000):
        if type(max_text_bytes) is not int or max_text_bytes<0 or type(max_entries) is not int or max_entries<0:
            raise ValueError('cache budget')
        self._entries=OrderedDict();self._bytes=0;self._pending=None
        self.max_text_bytes=max_text_bytes;self.max_entries=max_entries
        self.stats=dict(calls=0,hits=0,misses=0,evictions=0)
    def get(self,key):
        row=self._entries.get(key)
        if row is None:self.stats['misses']+=1;return None
        self.stats['hits']+=1
        return row[0]
    def stage(self,key,lines):self._pending.append((key,lines))
    def serialize(self,candidate,endpoint_path,identity_path,place_path,inventory):
        from model_inventory_snapshot_v1 import Snapshot
        if not isinstance(inventory,Snapshot):raise ValueError('owned immutable snapshot required')
        if self._pending is not None:raise RuntimeError('active serialization')
        self.stats['calls']+=1;self._pending=[]
        try:
            result=_serialize(candidate,endpoint_path,identity_path,place_path,inventory,self)
            for key,lines in self._pending:
                size=sum(len(line.encode('utf-8'))+1 for line in lines)
                if size>self.max_text_bytes or not self.max_entries:continue
                if key in self._entries:continue
                while self._entries and (self._bytes+size>self.max_text_bytes or len(self._entries)>=self.max_entries):
                    _,(_,old_size)=self._entries.popitem(last=False);self._bytes-=old_size;self.stats['evictions']+=1
                self._entries[key]=(lines,size);self._bytes+=size
            return result
        finally:self._pending=None
