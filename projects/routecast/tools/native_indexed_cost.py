"""Strict six-class single-segment VPR echo import; not router cost parity.

Echo decimal precision is finite. Only non-congestion indexed base cost is used;
criticality, RC, history, tree starting states and lookahead are not modeled.
"""
from decimal import Decimal,ROUND_HALF_UP
import xml.etree.ElementTree as ET
from compact_indexed_sketch import CompactIndexedSketch

def parse_cost_echo(text):
    lines=text.splitlines()
    if len(lines)<3 or not lines[0].startswith('Delay normalization factor: ') or not lines[1].startswith('Cost Index'):raise ValueError('invalid cost header')
    norm=Decimal(lines[0].split(':',1)[1].strip())
    if not norm.is_finite() or norm<=0:raise ValueError('invalid normalization')
    rows={}
    for line in lines[2:]:
        if not line.strip():continue
        fields=line.split()
        if len(fields)<9:raise ValueError('invalid row')
        index=int(fields[0]);kind=fields[1];name=' '.join(fields[2:-7]);base,ortho,segment,inv,linear,quadratic,load=fields[-7:]
        if index in rows or index<0 or kind not in {'SOURCE','SINK','OPIN','IPIN','CHANX','CHANY'}:raise ValueError('invalid cost class')
        values=[Decimal(v) for v in (base,linear,quadratic,load)]
        if any(not v.is_finite() or v<0 for v in values):raise ValueError('invalid cost/timing')
        inverse=Decimal(inv);channel=kind in {'CHANX','CHANY'}
        if channel and (not name or not inverse.is_finite() or inverse<=0):raise ValueError('invalid channel length/name')
        if not channel and (name or not inverse.is_nan()):raise ValueError('unsupported non-channel fields')
        rows[index]={'type':kind,'name':name,'base':values[0],'ortho':int(ortho),'segment':int(segment),'inverse_length':inverse}
    if set(rows)!=set(range(6)):raise ValueError('only single-segment six-class echoes supported')
    for i,kind in enumerate(('SOURCE','SINK','OPIN','IPIN','CHANX','CHANY')):
        r=rows[i]
        if r['type']!=kind or r['segment']!=(0 if i>=4 else -1) or r['ortho']!=({4:5,5:4}.get(i,-1)):raise ValueError('unsupported indexed class topology')
    if rows[4]['name']!=rows[5]['name'] or rows[4]['inverse_length']!=rows[5]['inverse_length']:raise ValueError('inconsistent single segment')
    return norm,rows

class NativeBaseSketch(CompactIndexedSketch):
    def __init__(self,graph,text,table_graph_sha256,scale=1000000):
        if table_graph_sha256!=graph.sha256:raise ValueError('cost graph identity mismatch')
        if type(scale) is not int or scale<1:raise ValueError('invalid cost scale')
        norm,rows=parse_cost_echo(text)
        if set(graph.segments)!={0} or ET.fromstring(graph.segments[0]).attrib.get('name')!=rows[4]['name']:raise ValueError('unsupported segment mapping')
        for node in graph.nodes.values():
            if int(dict(node.location).get('layer','0'))!=0:raise ValueError('unsupported multi-layer cost mapping')
            if node.type in {'CHANX','CHANY'} and node.segment_id!=0:raise ValueError('segment identity mismatch')
        super().__init__(graph,'rr_length_switch',len(graph.nodes))
        indexes={r['type']:i for i,r in rows.items()};node_cost={n:int((rows[indexes[v.type]]['base']/norm*scale).to_integral_value(rounding=ROUND_HALF_UP)) for n,v in graph.nodes.items()}
        self.outgoing={n:tuple((eid,dst,None if cost is None else node_cost[dst]) for eid,dst,cost in arcs) for n,arcs in self.outgoing.items()}
        self.node_costs=node_cost
