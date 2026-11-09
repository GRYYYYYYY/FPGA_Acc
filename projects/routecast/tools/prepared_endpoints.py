"""Packed pin/net identity and RR maps reused across placement projections.

Static file hashes are verified around each projection; unsupported mapping or
identity changes reject without modifying the prepared state. No route labels.
"""
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from pre_route_endpoints import extract,physical_maps,placements,sha
from pre_route_constants import extract_with_constants


class PreparedEndpoints:
    def __init__(self,net,graph,reference_place,*,atom=None,constant_net_method=None):
        if (atom is None)!=(constant_net_method is None):raise ValueError('atom and constant policy must be paired')
        self.net=Path(net);self.graph=Path(graph);self.atom=Path(atom) if atom is not None else None
        if self.atom is None:self.base,self.report=extract(net,reference_place,graph)
        else:self.base,self.report=extract_with_constants(net,reference_place,graph,atom,constant_net_method)
        self.static={k:v for k,v in self.base['inputs'].items() if k!='place'}
        self.connection_ids=defaultdict(list)
        for r in self.base['connections']:self.connection_ids[r['net_id']].append(r['connection_id'])
        self.types,self.grid,self.nodes=physical_maps(graph)
        root=ET.parse(net).getroot()
        self.logical={b.attrib['name']:re.sub(r'\[\d+\]$','',b.attrib['instance']) for b in root.findall('block')}
        self._verify()

    def _verify(self):
        for entry in self.static.values():
            if sha(entry['path'])!=entry['sha256']:raise ValueError('prepared static input identity changed')

    def project(self,place):
        self._verify();place=Path(place);before=sha(place)
        rows=placements(place,self.static['net']['sha256'])
        if set(rows)!=set(self.logical):raise ValueError('placement/cluster names differ')
        # Validate every cluster, including clusters with no external pin records.
        for name,(x,y,z,layer,bid) in rows.items():
            site=self.grid.get((x,y,layer))
            if site is None:raise ValueError('placement absent from RR grid')
            if site[1] or site[2]:raise ValueError('placement must use physical tile root')
        sources={};sinks=defaultdict(list);details=[]
        for pin in self.report['pin_details']:
            name=pin['block'];x,y,z,layer,bid=rows[name];tid=self.grid[(x,y,layer)][0]
            key=(self.logical[name],z,pin['port'],pin['bit']);physical=self.types[tid]['pins'].get(key)
            if physical is None:raise ValueError('unsupported logical/physical mapping')
            cls,direction,ptc=physical;role=pin['role']
            if direction!=('OUTPUT' if role=='SOURCE' else 'INPUT'):raise ValueError('physical pin direction mismatch')
            node=self.nodes.get((x,y,layer,cls,role))
            if node is None:raise ValueError('RR class endpoint missing')
            nid=pin['net_id']
            details.append({**pin,'block_id':bid,'physical_pin_ptc':ptc,'class_id':cls,'rr_node':node})
            if role=='SOURCE':
                if nid in sources:raise ValueError('multiple external drivers')
                sources[nid]=node
            else:sinks[nid].append(node)
        excluded={r['net_id'] for r in self.base['excluded_nets']};records=[]
        for text in self.base['net_names']:
            nid=int(text)
            if nid in excluded:continue
            if sinks[nid] and nid not in sources:raise ValueError('external net missing driver')
            if len(sinks[nid])!=len(self.connection_ids[nid]):raise ValueError('prepared connection multiplicity changed')
            for cid,sink in zip(self.connection_ids[nid],sinks[nid]):records.append({'connection_id':cid,'net_id':nid,'source':sources[nid],'sink':sink})
        result=deepcopy(self.base);result['connections']=records
        result['inputs']['place']={'path':str(place.resolve()),'sha256':before}
        result['reference_extractor_sha256']=self.base['source_sha256'];result['source_sha256']=sha(Path(__file__))
        result['provenance']='pre-route prepared packed pin and RR physical-map projection; no route input'
        self._verify()
        if sha(place)!=before:raise ValueError('placement changed during projection')
        return result,{**deepcopy(self.report),'pin_details':details,'connections':len(records),'source':'prepared pre-route maps, not route-derived'}
