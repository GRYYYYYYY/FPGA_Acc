"""Original XML witness audit with selected edge records, compact node arrays."""
from collections.abc import Mapping,Sequence
from types import SimpleNamespace
from array import array
import xml.etree.ElementTree as ET
from prepared_csr import TYPES
from pre_route_endpoints import sha
from physical_prediction_audit import audit

class Nodes(Mapping):
    def __init__(self,types,caps):self.types=types;self.caps=caps;self.names={v:k for k,v in TYPES.items()}
    def __len__(self):return len(self.types)
    def __iter__(self):return iter(range(len(self)))
    def __getitem__(self,n):
        if type(n) is not int or n<0 or n>=len(self):raise KeyError(n)
        return SimpleNamespace(type=self.names[self.types[n]],capacity=self.caps[n])
class Edges(Sequence):
    def __init__(self,records,count):self.records=records;self.count=count
    def __len__(self):return self.count
    def __getitem__(self,n):return self.records[n]

def verify(path,endpoints,prediction,topology=False):
    before=sha(path);wanted=set()
    for row in prediction['connections']:
        for eid in row['physical_edge_ids'] or ():
            if type(eid) is not int or eid<0:raise ValueError('invalid edge identity')
            wanted.add(eid)
    types=array('B');caps=array('Q');spans=array('Q');records={};count=0;stack=[]
    for event,e in ET.iterparse(path,events=('start','end')):
        if event=='start':
            stack.append(e)
            if len(stack)==1 and e.tag!='rr_graph':raise ValueError('expected RR root')
            continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            if int(e.get('id'))!=len(types):raise ValueError('contiguous ascending node IDs required')
            kind=e.get('type');capacity=int(e.get('capacity'));loc=e.find('loc')
            if capacity<0 or kind not in TYPES:raise ValueError('invalid node')
            types.append(TYPES[kind]);caps.append(capacity)
            spans.append(max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1)
        elif e.tag=='edge' and parent=='rr_edges':
            if count in wanted:records[count]=SimpleNamespace(source=int(e.get('src_node')),sink=int(e.get('sink_node')),switch_id=int(e.get('switch_id')))
            count+=1
        if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
        stack.pop()
    if wanted!=set(records):raise ValueError('unknown physical edge')
    graph=SimpleNamespace(nodes=Nodes(types,caps),edges=Edges(records,count),sha256=before)
    checked=audit(graph,endpoints,prediction)
    overuse=span=all_overuse=0
    for key,used in prediction['node_occupancy'].items():
        n=int(key)
        if used and not caps[n]:raise ValueError('disabled resource occupied')
        all_overuse+=max(0,used-caps[n])
        if types[n] in (TYPES['CHANX'],TYPES['CHANY']):
            span+=used*spans[n];overuse+=max(0,used-caps[n])
    if sha(path)!=before:raise ValueError('graph changed during audit')
    structural={}
    if topology:
        if checked['completed']==checked['requested']:
            from net_union_topology import diagnose
            structural['net_union_topology']=diagnose(graph,prediction)
        else:structural['net_union_topology']={'status':'not_evaluated_incomplete_paths'}
    return {**structural,**checked,'original_xml_edges':count,'selected_edges':len(records),'channel_net_span_sum':span,'predicted_channel_overuse_units':overuse,'all_type_overuse_units':all_overuse,'scope':'original XML individual paths and unique-net occupancy; no joint tree/pin legality or native QoR'}
