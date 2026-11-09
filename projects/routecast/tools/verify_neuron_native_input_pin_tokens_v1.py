"""Every native input/clock pin against the unchanged packed NET tokens."""
from collections import defaultdict
import json
from pathlib import Path
import resource
import sys
import time
import xml.etree.ElementTree as ET

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure


def main():
    resource.setrlimit(resource.RLIMIT_AS,(4*2**30,4*2**30));tick=time.perf_counter()
    src=R/'experiments/titan23_neuron_native_label_audit_v2_2026-10-15/canonical'
    records=[json.loads(line) for line in (src/'identity.jsonl').open()]
    expected=defaultdict(list)
    for r in records:
        for p in r['pins']:
            if p['index']>0:expected[p['block']].append((r['name'],r['ignored'],p['port'],p['bit']))
    checked=ignored=0;blocks=set();stack=[]
    for event,node in ET.iterparse(src/'design.net',events=('start','end')):
        if event=='start':stack.append(node);continue
        if node.tag=='block' and len(stack)==2:
            name=node.get('name');assert name not in blocks;blocks.add(name)
            ports={p.get('name'):(p.text or '').split() for section in ['inputs','clocks']
                   for p in node.findall(section+'/port')}
            for net,is_ignored,port,bit in expected.get(name,[]):
                assert ports[port][bit]==net,(name,port,bit,net,ports[port][bit])
                checked+=1;ignored+=is_ignored
            stack[-2].remove(node);node.clear()
        stack.pop()
    assert set(expected)<=blocks and checked==sum(len(v) for v in expected.values())
    assert sha(src/'design.net')==sha(src/'design.net.post_routing')
    bindings={**closure([Path(__file__)]),**{str(p):sha(p) for p in [src/'identity.jsonl',src/'design.net',src/'design.net.post_routing']}}
    out=R/'experiments/neuron_output_crossbar_realization_v1_2026-10-15/input_pin_verification.json'
    result=dict(bindings=bindings,all_pass=True,all_native_sink_pins=checked,ignored_sink_pins=ignored,
                nonignored_sink_pins=checked-ignored,all_input_and_clock_NET_tokens_identical=True,
                packed_netlist_byte_identical=True,label_accepted=False,
                seconds=time.perf_counter()-tick,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                scope='All native input/clock NET tokens in the original post-routing packed netlist, including every ignored sink. Combined output/canonical/physical admission remains external.')
    with out.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)


if __name__=='__main__':main()
