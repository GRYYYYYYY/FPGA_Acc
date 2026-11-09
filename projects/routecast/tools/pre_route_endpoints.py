"""SOURCE/SINK classes from packed .net, placement and RR XML only.

Supported mapping: logical pb port names match physical RR tile pin names;
subtile is encoded in the physical pin-name prefix. Ambiguous/unsupported
mappings fail rather than falling back to a routed endpoint. Clock policy is
explicit; this is not a general VPR logical-to-physical equivalent-site adapter.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

PIN=re.compile(r'^([^.[\]]+)(?:\[(\d+)\])?\.([^.[\]]+)\[(\d+)\]$')
REF=re.compile(r'^([^.]*)\.([^.[\]]+)\[(\d+)\]$')


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):digest.update(block)
    return digest.hexdigest()


def physical_maps(graph_path):
    types={}; grid={}; nodes={}; bounds={}; stack=[]
    for event,elem in ET.iterparse(graph_path,events=('start','end')):
        if event=='start':stack.append(elem);continue
        parent=stack[-2].tag if len(stack)>1 else None
        if elem.tag=='block_type' and parent=='block_types':
            tid=int(elem.attrib['id']); pins={}
            if tid in types:raise ValueError('duplicate block type')
            for cid,cls in enumerate(elem.findall('pin_class')):
                for pin in cls.findall('pin'):
                    name=(pin.text or '').strip();match=PIN.fullmatch(name)
                    if match is None:raise ValueError(f'unsupported physical pin name {name}')
                    key=(match[1],int(match[2] or 0),match[3],int(match[4]))
                    if key in pins:raise ValueError('ambiguous physical pin mapping')
                    pins[key]=(cid,cls.attrib['type'],int(pin.attrib['ptc']))
            types[tid]={'name':elem.attrib['name'],'pins':pins,'width':int(elem.attrib.get('width','1')),'height':int(elem.attrib.get('height','1'))}
        elif elem.tag=='grid_loc' and parent=='grid':
            key=tuple(int(elem.attrib.get(k,'0')) for k in ('x','y','layer'))
            if key in grid:raise ValueError('duplicate grid coordinate')
            grid[key]=tuple(int(elem.attrib[k]) for k in ('block_type_id','width_offset','height_offset'))
        elif elem.tag=='node' and parent=='rr_nodes' and elem.attrib['type'] in {'SOURCE','SINK'}:
            loc=elem.find('loc')
            if loc is None:raise ValueError('missing endpoint loc')
            # A hard-block class bbox may start inside its physical tile.
            if int(loc.attrib['xhigh'])<int(loc.attrib['xlow']) or int(loc.attrib['yhigh'])<int(loc.attrib['ylow']):
                raise ValueError('invalid endpoint bounds')
            key=tuple(int(loc.attrib.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))+(elem.attrib['type'],)
            if key in nodes:raise ValueError('ambiguous RR endpoint class')
            nodes[key]=int(elem.attrib['id'])
            bounds[key]=(int(loc.attrib['xhigh']),int(loc.attrib['yhigh']))
        if (elem.tag,parent) in {('block_type','block_types'),('grid_loc','grid'),('node','rr_nodes'),('edge','rr_edges')}:
            stack[-2].remove(elem);elem.clear()
        stack.pop()
    if not types or not grid or not nodes:raise ValueError('missing physical mapping sections')
    rooted={}
    for key,nid in nodes.items():
        x,y,layer,cid,kind=key
        if (x,y,layer) not in grid:raise ValueError('endpoint absent from grid')
        tid,wo,ho=grid[(x,y,layer)];rx,ry=x-wo,y-ho
        if grid.get((rx,ry,layer))!=(tid,0,0):raise ValueError('invalid endpoint tile root')
        tile=types[tid];xh,yh=bounds[key]
        if not (0<=wo<tile['width'] and 0<=ho<tile['height'] and xh<rx+tile['width'] and yh<ry+tile['height']):raise ValueError('endpoint bbox crosses physical tile')
        canonical=(rx,ry,layer,cid,kind)
        if canonical in rooted:raise ValueError('ambiguous rooted RR endpoint class')
        rooted[canonical]=nid
    return types,grid,rooted


def placements(path,net_sha):
    rows={};slots=set(); checked=False
    for raw in Path(path).read_text().splitlines():
        line=raw.strip()
        if not line or line.startswith('#') or line.startswith('Array size:'):continue
        if line.startswith('Netlist_File:'):
            match=re.search(r'Netlist_ID:\s*SHA256:([0-9a-f]{64})',line)
            if match is None or match[1]!=net_sha:raise ValueError('placement netlist identity mismatch')
            checked=True;continue
        fields=line.split()
        if len(fields)<6 or not fields[5].startswith('#'):raise ValueError('unsupported placement row')
        name=fields[0];x,y,z,layer=map(int,fields[1:5]);bid=int(fields[5][1:])
        if name in rows or (x,y,z,layer) in slots or min(x,y,z,layer,bid)<0:
            raise ValueError('duplicate/invalid placement')
        rows[name]=(x,y,z,layer,bid);slots.add((x,y,z,layer))
    if not checked or not rows:raise ValueError('missing placement identity/rows')
    return rows


class PhysicalMapContext:
    """Hash-bound read-only RR mapping; graph hashing remains per extraction."""
    def __init__(self, graph_path):
        from types import MappingProxyType
        def freeze(value):
            if isinstance(value, dict):
                return MappingProxyType({key: freeze(v) for key, v in value.items()})
            if isinstance(value, tuple):
                return tuple(freeze(v) for v in value)
            return value
        digest = sha(graph_path)
        self._maps = freeze(physical_maps(graph_path))
        if sha(graph_path) != digest:
            raise ValueError('graph changed during mapping preparation')
        self._digest = digest

    def maps(self, digest):
        if digest != self._digest:
            raise ValueError('prepared physical mapping graph mismatch')
        return self._maps


def extract(net_path,place_path,graph_path,clock_policy='exclude_root_clocks', *, physical_context=None):
    if clock_policy!='exclude_root_clocks':raise ValueError('unsupported clock policy')
    input_before={k:sha(p) for k,p in [('net',net_path),('place',place_path),('graph',graph_path)]}
    net_sha=input_before['net']; place=placements(place_path,net_sha)
    if physical_context is not None and type(physical_context) is not PhysicalMapContext:
        raise ValueError('invalid physical mapping context')
    types,grid,rr_nodes=(physical_maps(graph_path) if physical_context is None else
                       physical_context.maps(input_before['graph']))
    root=ET.parse(net_path).getroot();clusters=root.findall('block')
    if set(place)!={b.attrib['name'] for b in clusters}:raise ValueError('placement/cluster names differ')
    parents={child:parent for parent in root.iter('block') for child in parent.findall('block')}
    memo={}
    def resolve(block,port,index,active=frozenset()):
        key=(block,port,index)
        if key in active:raise ValueError('packed pin reference cycle')
        if key in memo:return memo[key]
        ports=[p for section in ('inputs','outputs','clocks') for p in block.findall(f'{section}/port') if p.attrib['name']==port]
        if len(ports)!=1:raise ValueError(f'missing/ambiguous packed port {port}')
        tokens=(ports[0].text or '').split()
        if index>=len(tokens):raise ValueError('packed port index out of range')
        token=tokens[index]
        if token=='open':value=None
        elif '->' not in token:value=token
        else:
            ref=token.split('->',1)[0];match=REF.fullmatch(ref)
            if match is None:raise ValueError(f'unsupported packed reference {ref}')
            instance,pname,pindex=match[1],match[2],int(match[3])
            candidates=[c for c in block.findall('block') if c.attrib['instance']==instance]
            if not candidates:
                context=block
                while context is not None:
                    own=context.attrib['instance']
                    if instance in {own,re.sub(r'\[\d+\]$','',own)}:
                        candidates=[context];break
                    context=parents.get(context)
            if len(candidates)!=1:raise ValueError(f'packed reference context unresolved: {ref}')
            value=resolve(candidates[0],pname,pindex,active|{key})
        memo[key]=value;return value
    nets={};sources={};sinks=defaultdict(list);pin_details=[]
    clock_nets=set((root.findtext('clocks') or '').split())
    for block in clusters:
        name=block.attrib['name'];x,y,z,layer,bid=place[name]
        logical=re.sub(r'\[\d+\]$','',block.attrib['instance'])
        site=grid.get((x,y,layer))
        if site is None:raise ValueError('placement absent from RR grid')
        tid,wo,ho=site
        if wo or ho:raise ValueError('placement must use physical tile root')
        for section,kind,cls_kind in [('inputs','SINK','INPUT'),('outputs','SOURCE','OUTPUT'),('clocks','SINK','INPUT')]:
            for port in block.findall(f'{section}/port'):
                for index,token in enumerate((port.text or '').split()):
                    if token=='open':continue
                    net=resolve(block,port.attrib['name'],index)
                    if net is None:raise ValueError('connected root port resolves to open')
                    if net not in nets:nets[net]=len(nets)
                    key=(logical,z,port.attrib['name'],index)
                    physical=types[tid]['pins'].get(key)
                    if physical is None:raise ValueError(f'unsupported logical/physical mapping: {name} {key}')
                    cid,direction,ptc=physical
                    if direction!=cls_kind:raise ValueError('physical pin direction mismatch')
                    rr=rr_nodes.get((x,y,layer,cid,kind))
                    if rr is None:raise ValueError(f'RR class endpoint missing: block={name} net={net} physical_pin={key} rr_key={(x,y,layer,cid,kind)} root_clock={net in clock_nets}')
                    detail={'net':net,'net_id':nets[net],'block':name,'block_id':bid,'port':port.attrib['name'],
                            'bit':index,'physical_pin_ptc':ptc,'class_id':cid,'rr_node':rr,'role':kind}
                    pin_details.append(detail)
                    if kind=='SOURCE':
                        if net in sources:raise ValueError(f'multiple external drivers: {net}')
                        sources[net]=rr
                    else:sinks[net].append(rr)
    records=[]; excluded=[]
    for net,nid in nets.items():
        if net in clock_nets:
            excluded.append({'net':net,'net_id':nid,'reason':'explicit exclude_root_clocks policy','sink_pins':len(sinks[net])});continue
        if sinks[net] and net not in sources:raise ValueError(f'external net missing driver: {net}')
        for sink in sinks[net]:
            records.append({'connection_id':len(records),'net_id':nid,'source':sources[net],'sink':sink})
    result={'schema':'ROUTECAST_ENDPOINTS_V1','graph_sha256':sha(graph_path),
            'provenance':'pre-route packed netlist and placement physical pin-class mapping; no route input',
            'connections':records,'net_names':{str(n):name for name,n in nets.items()},
            'excluded_nets':excluded,'clock_policy':clock_policy,
            'inputs':{k:{'path':str(Path(p).resolve()),'sha256':sha(p)} for k,p in [('net',net_path),('place',place_path),('graph',graph_path)]}}
    if any(result['inputs'][k]['sha256']!=digest for k,digest in input_before.items()):
        raise ValueError('input changed during extraction')
    result['source_sha256']=sha(Path(__file__))
    return result,{'pin_details':pin_details,'external_nets':len(nets),'connections':len(records),
                   'excluded_nets':excluded,'source':'pre-route physical pin mapping, not route-derived'}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for field in ('net','place','graph'):p.add_argument(field,type=Path)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--mapping-report',type=Path,required=True)
    a=p.parse_args();result,report=extract(a.net,a.place,a.graph)
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n')
    report['source_sha256']=sha(Path(__file__))
    a.mapping_report.parent.mkdir(parents=True,exist_ok=True);a.mapping_report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'connections':len(result['connections']),'nets':report['external_nets'],'excluded':len(result['excluded_nets'])}))
