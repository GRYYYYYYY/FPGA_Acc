"""Bounded XML parsing, columnar node views and exact class-coded increments.

No routing demand is removed. CSR preserves ascending source ID and original
per-source XML edge order, including graphs whose XML edges are unsorted.
Node views retain every attribute and ordered direct leaf child; unsupported
nested/text-bearing node metadata is rejected explicitly, never discarded.
"""
import json
import xml.etree.ElementTree as E
from array import array
from collections.abc import Sequence
from math import lcm
from pathlib import Path
from types import MappingProxyType
from pre_route_endpoints import sha
from path_rc import number
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC as IntegerBase

class NodeView:
    __slots__=('owner','index','tag')
    def __init__(self,owner,index,tag='node'):self.owner,self.index,self.tag=owner,index,tag
    def get(self,key,default=None):
        if self.tag=='node' and key=='id':return str(self.index)
        column=self.owner.columns.get((self.tag,key))
        value=0 if column is None else column[self.index]
        return self.owner.strings[value] if value else default
    @property
    def attrib(self):
        result={key:self.get(key) for tag,key in self.owner.columns if tag==self.tag and self.get(key) is not None}
        if self.tag=='node':result['id']=str(self.index)
        return MappingProxyType(result)
    def __iter__(self):
        if self.tag=='node':
            for tag in self.owner.orders[self.owner.order_ids[self.index]]:yield NodeView(self.owner,self.index,tag)
    def find(self,path):
        if self.tag!='node' or '/' in path:return None
        if path in self.owner.orders[self.owner.order_ids[self.index]]:return NodeView(self.owner,self.index,path)
        return None

class Nodes(Sequence):
    def __init__(self):
        self.strings=[None];self.lookup={};self.columns={};self.orders=[];self.order_lookup={};self.order_ids=array('I');self.frozen=False
    def __len__(self):return len(self.order_ids)
    def __getitem__(self,i):
        if isinstance(i,slice):return [self[j] for j in range(*i.indices(len(self)))]
        if i<0:i+=len(self)
        if not 0<=i<len(self):raise IndexError(i)
        return NodeView(self,i)
    def append(self,node):
        if self.frozen:raise RuntimeError('frozen node columns')
        n=len(self)
        if node.get('id')!=str(n):raise ValueError('contiguous node IDs required')
        tags=tuple(child.tag for child in node)
        if len(set(tags))!=len(tags) or any(len(c) or c.text and c.text.strip() for c in node) or node.text and node.text.strip():
            raise ValueError('unsupported nested/duplicate/text node metadata')
        if tags not in self.order_lookup:self.order_lookup[tags]=len(self.orders);self.orders.append(tags)
        for values in self.columns.values():values.append(0)
        for item in [node,*node]:
            for key,value in item.attrib.items():
                if item is node and key=='id':continue
                k=(item.tag,key)
                if k not in self.columns:self.columns[k]=array('I',[0])*(n+1)
                if value not in self.lookup:self.lookup[value]=len(self.strings);self.strings.append(value)
                self.columns[k][n]=self.lookup[value]
        self.order_ids.append(self.order_lookup[tags])
    def freeze(self):
        self.columns=MappingProxyType({k:memoryview(v).toreadonly() for k,v in self.columns.items()})
        self.strings=tuple(self.strings);self.orders=tuple(self.orders);self.order_ids=memoryview(self.order_ids).toreadonly()
        self.lookup=None;self.order_lookup=None;self.frozen=True

class EncodedCosts(Sequence):
    def __init__(self,codes,values):self.codes=memoryview(codes).toreadonly();self.values=tuple(values)
    def __len__(self):return len(self.codes)
    def __getitem__(self,i):
        if isinstance(i,slice):return tuple(self.values[k] for k in self.codes[i])
        return self.values[self.codes[i]]

class IntegerRC(IntegerBase):
    def __init__(self,rc):
        self.rc=rc;self.fields=rc.fields
        initials={c:rc.classes[c][0]*rc.classes[c][1]/2 for c in set(rc.node_classes)}
        pair_ids={};pairs=[];codes=array('I')
        for v,switch in zip(self.fields['dest_ranks'],self.fields['switch_ids']):
            key=(rc.node_classes[v],switch)
            code=pair_ids.get(key)
            if code is None:
                from buffered_rc_node_classes import arc_delay
                code=len(pairs);pair_ids[key]=code;pairs.append(arc_delay(rc.classes,rc.switches,*key))
                rc.cache[key]=pairs[-1]
            codes.append(code)
        self.scale=lcm(1,*(v.denominator for v in initials.values()),*(v.denominator for v in pairs))
        self.increments=EncodedCosts(codes,[self.encode(v) for v in pairs])
        self.initial_by_class={k:self.encode(v) for k,v in initials.items()}
    def initial(self,n):
        if type(n) is not int or not 0<=n<len(self.rc.node_classes):raise ValueError('invalid raw node')
        return self.initial_by_class[self.rc.node_classes[n]]

def load_endpoints(endpoint_path):
    endpoint=json.loads(Path(endpoint_path).read_text())
    if not all(sha(v['path'])==v['sha256'] for v in endpoint['inputs'].values()):raise ValueError('changed endpoint input')
    graph=Path(endpoint['inputs']['graph']['path']);digest=sha(graph)
    if digest!=endpoint['graph_sha256']:raise ValueError('graph identity')
    nodes=Nodes();classes=[];lookup={};indices=array('I');switches={};stack=[]
    sources=array('Q');dest=array('Q');switch_ids=array('Q');caps=array('Q')
    monotone=True;previous=-1;nodes_done=False
    for event,node in E.iterparse(graph,events=('start','end')):
        if event=='start':
            stack.append(node)
            if len(stack)==1 and node.tag!='rr_graph':raise ValueError('RR root')
            continue
        parent=stack[-2].tag if len(stack)>1 else None
        if node.tag=='node' and parent=='rr_nodes':
            nodes.append(node);caps.append(int(node.get('capacity')))
            timing=node.find('timing')
            if timing is None or not {'R','C'}<=set(timing.attrib):raise ValueError('missing RC')
            key=(timing.get('R'),timing.get('C'))
            if key not in lookup:
                values=tuple(map(number,key))
                if min(values)<0:raise ValueError('negative node RC')
                lookup[key]=len(classes);classes.append(values)
            indices.append(lookup[key]);stack[-2].remove(node);node.clear()
        elif node.tag=='rr_nodes':nodes_done=True
        elif node.tag=='switch' and parent=='switches':
            sid=int(node.get('id'));timing=node.find('timing')
            if sid<0 or sid in switches or timing is None or node.get('type') not in {'buffer','mux','tristate'}:raise ValueError('switch domain')
            if number(timing.get('Cinternal','0')):raise ValueError('nonzero Cinternal')
            value=(number(timing.get('R','0')),number(timing.get('Tdel','0')))
            if min(value)<0:raise ValueError('negative switch RC')
            switches[sid]=value;stack[-2].remove(node);node.clear()
        elif node.tag=='edge' and parent=='rr_edges':
            u,v,s=int(node.get('src_node')),int(node.get('sink_node')),int(node.get('switch_id'))
            if not nodes_done or not 0<=u<len(nodes) or not 0<=v<len(nodes):raise ValueError('edge node identity/order')
            sources.append(u);dest.append(v);switch_ids.append(s)
            monotone=monotone and u>=previous;previous=u
            stack[-2].remove(node);node.clear()
        elif node.tag=='segment' and parent=='segments':stack[-2].remove(node);node.clear()
        stack.pop()
    if not indices or not switches:raise ValueError('empty electrical domain')
    if any(s not in switches for s in switch_ids):raise ValueError('unknown switch')
    nodes.freeze();n=len(nodes);m=len(dest)
    offsets=array('Q',[0])*(n+1)
    for u in sources:offsets[u+1]+=1
    for u in range(n):offsets[u+1]+=offsets[u]
    edge_ids=array('Q',range(m))
    if not monotone:
        ordered_dest=array('Q',[0])*m;ordered_switch=array('Q',[0])*m
        next_slot=array('Q',offsets)
        for eid,(u,v,s) in enumerate(zip(sources,dest,switch_ids)):
            slot=next_slot[u];next_slot[u]+=1
            ordered_dest[slot]=v;ordered_switch[slot]=s;edge_ids[slot]=eid
        dest,switch_ids=ordered_dest,ordered_switch
    del sources
    fields=dict(node_ids=array('Q',range(n)),row_offsets=offsets,dest_ranks=dest,edge_ids=edge_ids,
                switch_ids=switch_ids,costs=array('Q',[1])*m,capacities=caps)
    rc=IntegerRC(ExactBufferedRC(fields,indices,classes,switches))
    if sha(graph)!=digest:raise ValueError('graph changed during load')
    return graph,digest,nodes,fields,rc,endpoint['connections']
