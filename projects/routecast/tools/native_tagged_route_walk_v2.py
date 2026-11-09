"""Walk original route text using explicit SINK pin tags and branch restoration."""
import re
from stream_native_NET_occupancy_v1 import NET,NODE
PIN=re.compile(r'\bNet_pin_index:\s*(\d+)\b')


def walk(path):
    net=source=current=switch=None;seen=set();headers=set()
    with open(path) as stream:
        for line in stream:
            match=NET.match(line)
            if match:
                net=int(match[1]);assert net not in headers;headers.add(net)
                source=current=switch=None;seen=set()
                yield ('net',net,match[2]);continue
            if line.lstrip().startswith('Net '):raise ValueError('Unrecognized NET header')
            match=NODE.match(line)
            if match is None:
                if line.lstrip().startswith('Node:'):raise ValueError('Unrecognized route node')
                continue
            assert net is not None
            nid=int(match[1]);kind=match[2];outgoing=int(match[3])
            if kind=='SOURCE':
                if source is None:assert not seen
                else:assert source==nid and nid in seen
                source=nid;yield ('source',net,nid)
            elif nid not in seen or kind=='SINK':
                assert source is not None and current is not None and switch is not None and switch>=0
                yield ('arc',net,current,nid,switch)
            seen.add(nid);current=nid;switch=outgoing
            if kind=='SINK':
                pin=PIN.search(line)
                if pin is None:raise ValueError('Missing explicit SINK Net_pin_index')
                yield ('sink',net,source,nid,int(pin[1]))
