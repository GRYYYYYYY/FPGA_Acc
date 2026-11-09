"""Strict, independent VPR RR XML reader; preserves raw resource semantics."""
import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class RRNode:
    id: int
    type: str
    capacity: int
    direction: str
    attributes: tuple
    location: tuple
    timing: tuple
    segment_id: int | None


@dataclass(frozen=True)
class RREdge:
    source: int
    sink: int
    switch_id: int
    attributes: tuple


@dataclass(frozen=True)
class RRGraph:
    nodes: dict
    edges: tuple
    switches: dict
    segments: dict
    metadata: dict
    sha256: str

    def summary(self):
        return {'schema':'ROUTECAST_RR_AUDIT_V1','sha256':self.sha256,
                'metadata':dict(self.metadata),'node_count':len(self.nodes),'edge_count':len(self.edges),
                'switch_count':len(self.switches),'segment_count':len(self.segments),
                'node_types':dict(Counter(n.type for n in self.nodes.values())),
                'directions':dict(Counter(n.direction for n in self.nodes.values())),
                'zero_capacity_nodes':sum(n.capacity == 0 for n in self.nodes.values()),
                'scope':'XML resource integrity, not route legality or prediction quality'}


def read_rr_graph(path):
    path = Path(path)
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''): digest.update(block)
    nodes, edges, switches, segments, metadata = {}, [], {}, {}, {}
    stack = []
    with path.open('rb') as stream:
        for event, elem in ET.iterparse(stream,events=('start','end')):
            if event == 'start':
                stack.append(elem)
                if len(stack)==1:
                    if elem.tag != 'rr_graph': raise ValueError('expected rr_graph root')
                    metadata=dict(elem.attrib)
                continue
            parent = stack[-2].tag if len(stack)>1 else None
            tag=elem.tag
            if tag=='node' and parent=='rr_nodes':
                nid=int(elem.attrib['id']); capacity=int(elem.attrib['capacity'])
                kind=elem.attrib['type']; direction=elem.attrib.get('direction','NONE')
                loc=elem.find('loc'); timing=elem.find('timing'); segment=elem.find('segment')
                if nid<0 or nid in nodes or capacity<0 or loc is None:
                    raise ValueError('invalid/duplicate node or missing location')
                if kind not in {'SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'}:
                    raise ValueError('unsupported node type')
                if direction not in {'NONE','INC_DIR','DEC_DIR','BI_DIR'}:
                    raise ValueError('unsupported direction')
                for low,high in [('xlow','xhigh'),('ylow','yhigh')]:
                    if int(loc.attrib[low])<0 or int(loc.attrib[high])<int(loc.attrib[low]):
                        raise ValueError('invalid node bounds')
                if int(loc.attrib['ptc'])<0: raise ValueError('invalid ptc')
                sid=None if segment is None else int(segment.attrib['segment_id'])
                if kind in {'CHANX','CHANY'} and sid is None: raise ValueError('channel missing segment')
                nodes[nid]=RRNode(nid,kind,capacity,direction,tuple(sorted(elem.attrib.items())),
                                  tuple(sorted(loc.attrib.items())),
                                  tuple(sorted(timing.attrib.items())) if timing is not None else (),sid)
            elif tag=='edge' and parent=='rr_edges':
                edges.append(RREdge(int(elem.attrib['src_node']),int(elem.attrib['sink_node']),
                                    int(elem.attrib['switch_id']),tuple(sorted(elem.attrib.items()))))
            elif (tag,parent) in {('switch','switches'),('segment','segments')}:
                target=switches if tag=='switch' else segments
                rid=int(elem.attrib['id'])
                if rid<0 or rid in target: raise ValueError('invalid/duplicate semantic record')
                target[rid]=ET.tostring(elem,encoding='unicode')
            if tag in {'node','edge','switch','segment'} and parent in {'rr_nodes','rr_edges','switches','segments'}:
                stack[-2].remove(elem); elem.clear()
            stack.pop()
    if not nodes: raise ValueError('empty RR graph')
    for node in nodes.values():
        if node.segment_id is not None and node.segment_id not in segments:
            raise ValueError('unknown segment')
    for edge in edges:
        if edge.source not in nodes or edge.sink not in nodes or edge.switch_id not in switches:
            raise ValueError('unknown edge endpoint or switch')
    return RRGraph(MappingProxyType(nodes),tuple(edges),MappingProxyType(switches),
                   MappingProxyType(segments),MappingProxyType(metadata),digest.hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('xml',type=Path)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    graph=read_rr_graph(args.xml); summary=graph.summary()
    summary['source_path']=str(args.xml.resolve())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('node_count','edge_count','sha256')}))
