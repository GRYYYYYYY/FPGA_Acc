"""Exact node RC classes for immutable host CSR budget searches."""
from array import array
import xml.etree.ElementTree as ET
from path_rc import number
from pre_route_endpoints import sha

def read(path):
    before=sha(path);indices=array('Q');classes=[];lookup={};switches={};stack=[]
    for event,e in ET.iterparse(path,events=('start','end')):
        if event=='start':
            stack.append(e)
            if len(stack)==1 and e.tag!='rr_graph':raise ValueError('expected RR root')
            continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            if int(e.get('id'))!=len(indices):raise ValueError('contiguous node IDs required')
            timing=e.find('timing')
            if timing is None or not {'R','C'}<=set(timing.attrib):raise ValueError('missing node RC')
            key=(timing.get('R'),timing.get('C'))
            if key not in lookup:
                resistance,capacitance=map(number,key);lookup[key]=len(classes);classes.append((resistance,capacitance))
            indices.append(lookup[key])
        elif e.tag=='switch' and parent=='switches':
            sid=int(e.get('id'));timing=e.find('timing')
            if sid<0 or sid in switches or timing is None:raise ValueError('invalid switch')
            if e.get('type') not in {'buffer','mux','tristate'}:raise ValueError('nonbuffered switch')
            if number(timing.get('Cinternal','0')):raise ValueError('nonzero Cinternal')
            switches[sid]=(number(timing.get('R','0')),number(timing.get('Tdel','0')))
        if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):stack[-2].remove(e);e.clear()
        stack.pop()
    if not indices or not switches:raise ValueError('empty electrical context')
    if sha(path)!=before:raise ValueError('graph changed')
    return indices,classes,switches,before

def arc_delay(classes,switches,node_class,switch_id):
    resistance,capacitance=classes[node_class];sr,intrinsic=switches[switch_id]
    return (sr+resistance/2)*capacitance+intrinsic
