"""Restricted Python replica of this VPR revision's print_place formatting."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import placements, sha

def canonical_place(place_path, net_path):
    place_path,net_path=Path(place_path),Path(net_path)
    rows=placements(place_path,sha(net_path))
    lines=place_path.read_text().splitlines()
    header=f'Netlist_File: design.net Netlist_ID: SHA256:{sha(net_path)}'
    if lines[0]!=header or not re.fullmatch(r'Array size: \d+ x \d+ logic blocks',lines[1]):
        raise ValueError('unsupported placement header')
    blocks=ET.parse(net_path).getroot().findall('block')
    names=[b.attrib['name'] for b in blocks]
    if len(set(names))!=len(names) or set(names)!=set(rows):
        raise ValueError('packed block set mismatch')
    output=[header,lines[1],'','#block name\tx\ty\tsubblk\tlayer\tblock number',
            '#----------\t--\t--\t------\t-----\t------------']
    for bid,name in enumerate(names):
        x,y,z,layer,actual=rows[name]
        if actual!=bid or any(c.isspace() for c in name):
            raise ValueError('unsupported block identity')
        output.append(name+'\t'+('\t' if len(name.encode('utf-8'))<8 else '')+
                      f'{x}\t{y}\t{z}\t{layer}\t#{bid}')
    return '\n'.join(output)+'\n'
