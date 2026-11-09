"""XML -> additive CSR using existing native binding validation and exact costs."""
from collections.abc import Mapping
from types import SimpleNamespace
from fractions import Fraction
import xml.etree.ElementTree as ET
from streaming_rr_nodes import read
from streaming_cached_arc_cost import StreamingCachedArcCost
from streaming_csr_builder import write
from bound_indexed_cost import validate_binding
from prepared_csr import TYPES,U64
from pre_route_endpoints import sha

class Nodes(Mapping):
    def __init__(self,fields):
        self.fields=fields;self.rank={n:i for i,n in enumerate(fields['node_ids'])};self.types={v:k for k,v in TYPES.items()}
    def __iter__(self):return iter(self.rank)
    def __len__(self):return len(self.rank)
    def __getitem__(self,n):
        i=self.rank[n];f=self.fields
        return SimpleNamespace(type=self.types[f['types'][i]],segment_id=None if f['segments'][i]==U64 else f['segments'][i],location=(('layer',str(f['layer'][i])),))

def convert(path,text,bindings_csv,identity,out,scale=10**6,*,class_cache=False):
    if type(class_cache) is not bool:raise ValueError('class_cache must be boolean')
    fields,r,c,switches,segments,graph_sha=read(path)
    nodes=Nodes(fields)
    graph=SimpleNamespace(nodes=nodes,segments=segments,sha256=graph_sha)
    norm,rows,indices,expected=validate_binding(graph,text,bindings_csv,identity)
    bases={i:Fraction(row['base']) for i,row in rows.items()}
    if class_cache:
        from prepared_streaming_arc_cost import PreparedStreamingArcCost
        costs=PreparedStreamingArcCost(switches,bases,norm,r,c,[indices[n] for n in fields['node_ids']],fields['capacities'],scale)
    else:costs=StreamingCachedArcCost(switches,bases,norm,scale)
    def arcs():
        stack=[];eid=0
        for event,e in ET.iterparse(path,events=('start','end')):
            if event=='start':stack.append(e);continue
            parent=stack[-2].tag if len(stack)>1 else None
            if e.tag=='edge' and parent=='rr_edges':
                src=int(e.get('src_node'));dst=int(e.get('sink_node'));sid=int(e.get('switch_id'))
                if src not in nodes.rank or dst not in nodes.rank:raise ValueError('unknown edge endpoint')
                a=nodes.rank[src];b=nodes.rank[dst]
                cost=costs.cost(sid,a,b) if class_cache else costs.cost(sid,r[a],r[b],c[b],indices[dst],fields['capacities'][b])
                yield eid,src,dst,sid,cost
                eid+=1
            if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):
                stack[-2].remove(e);e.clear()
            stack.pop()
        if sha(path)!=graph_sha:raise ValueError('graph changed during arc traversal')
    context={'graph_sha256':graph_sha,'cost_identity':expected,'scale':scale,'normalization':str(Fraction(norm)),'mode':'rr_length_switch'}
    return write(fields,arcs,out,context)
