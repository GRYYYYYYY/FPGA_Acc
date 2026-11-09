"""Compact sorted-ID RR node inventory; no permanent node/edge objects."""
from array import array
import xml.etree.ElementTree as ET
from prepared_csr import TYPES,DIRECTIONS,SIDES,U64
from path_rc import number
from pre_route_endpoints import sha

def read(path):
    before=sha(path)
    names=('node_ids','types','directions','sides','capacities','segments','xlow','xhigh','ylow','yhigh','layer','ptc')
    fields={n:array('B' if n in ('types','directions','sides') else 'q' if n in ('xlow','xhigh','ylow','yhigh','layer','ptc') else 'Q') for n in names}
    resistance=[];capacitance=[];switches={};segments={};stack=[]
    for event,e in ET.iterparse(path,events=('start','end')):
        if event=='start':
            stack.append(e)
            if len(stack)==1 and e.tag!='rr_graph':raise ValueError('expected rr_graph root')
            continue
        parent=stack[-2].tag if len(stack)>1 else None
        if e.tag=='node' and parent=='rr_nodes':
            nid=int(e.get('id'));cap=int(e.get('capacity'));loc=e.find('loc');seg=e.find('segment');tim=e.find('timing')
            if nid<0 or cap<0 or loc is None:raise ValueError('invalid node/location')
            if fields['node_ids'] and nid<=fields['node_ids'][-1]:raise ValueError('sorted unique node IDs required')
            kind=e.get('type');direction=e.get('direction','NONE');side=loc.get('side','NONE')
            if kind not in TYPES or direction not in DIRECTIONS or side not in SIDES:raise ValueError('invalid node enum')
            sid=U64 if seg is None else int(seg.get('segment_id'))
            if sid<0 or (kind in ('CHANX','CHANY') and sid==U64):raise ValueError('invalid channel segment')
            coords={n:int(loc.get(n,'0')) for n in ('xlow','xhigh','ylow','yhigh','layer','ptc')}
            if any(n not in loc.attrib for n in ('xlow','xhigh','ylow','yhigh','ptc')):raise ValueError('missing location field')
            if coords['xlow']<0 or coords['ylow']<0 or coords['xhigh']<coords['xlow'] or coords['yhigh']<coords['ylow'] or coords['ptc']<0:raise ValueError('invalid node bounds')
            if tim is None:raise ValueError('missing node timing')
            resistance.append(number(tim.get('R','0')));capacitance.append(number(tim.get('C','0')))
            values={'node_ids':nid,'types':TYPES[kind],'directions':DIRECTIONS[direction],'sides':SIDES[side],'capacities':cap,'segments':sid,**coords}
            for n in names:fields[n].append(values[n])
        elif (e.tag,parent) in (('switch','switches'),('segment','segments')):
            target=switches if e.tag=='switch' else segments;rid=int(e.get('id'))
            if rid<0 or rid in target:raise ValueError('invalid duplicate semantic record')
            target[rid]=ET.tostring(e,encoding='unicode')
        if (e.tag,parent) in (('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')):
            stack[-2].remove(e);e.clear()
        stack.pop()
    if not fields['node_ids']:raise ValueError('empty graph')
    if any(s!=U64 and s not in segments for s in fields['segments']):raise ValueError('unknown segment')
    if sha(path)!=before:raise ValueError('graph changed during inventory')
    return fields,resistance,capacitance,switches,segments,before
