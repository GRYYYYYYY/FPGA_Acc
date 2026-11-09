"""Independent binary32 mantissa/exponent rebuild and all-node u128 payload audit."""
import json
import struct
import sys
import xml.etree.ElementTree as E
from collections import Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

def audit(proof_path):
    proof_path=Path(proof_path).resolve();v=json.loads(proof_path.read_text())
    assert v['payload_format']=='unsigned128_little_endian'
    assert v['all_original_node_ids_types_segments_and_native_group_counts_pass']
    bindings={**v['bindings'],str(proof_path):sha(proof_path),str(Path(__file__).resolve()):sha(Path(__file__))}
    assert all(sha(p)==h for p,h in bindings.items())
    table=next(Path(p) for p in bindings if p.endswith('/indexed.tsv'))
    graphs=[Path(p) for p in bindings if p.endswith('/rr_graph.xml')]
    assert len(graphs)==1;graph=graphs[0]
    rows=[x.split() for x in table.read_text().splitlines()];indexed={int(x[1]):x for x in rows if x[0]=='I'}
    types=['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'];mapping={};expected=Counter()
    for row in rows:
        if row[0]!='N':continue
        kind,index,count=map(int,row[1:]);r=indexed[index]
        bits=int.from_bytes(struct.pack('!f',float(r[3])),'big')
        exponent=(bits>>23)&255;mantissa=bits&((1<<23)-1)
        assert not bits>>31 and exponent!=255
        if exponent:mantissa+=1<<23;power=exponent-150
        else:power=-149
        exact=Fraction(mantissa)*Fraction(2)**power*v['scale']
        integer=(exact.numerator+exact.denominator-1)//exact.denominator
        assert integer-1<exact<=integer and 0<=integer<2**120
        key=(types[kind],int(r[2]));assert key not in mapping
        mapping[key]=integer;expected[key]=count
    payload=proof_path.parent/v['payload_file'];assert str(payload) in bindings
    counts=Counter();stack=[];n=0;over64=0
    with payload.open('rb') as source:
        for event,node in E.iterparse(graph,events=('start','end')):
            if event=='start':stack.append(node);continue
            if node.tag=='node':
                assert node.get('id')==str(n);seg=node.find('segment')
                key=(node.get('type'),int(seg.get('segment_id')) if seg is not None else -1)
                word=source.read(16);assert len(word)==16
                value=int.from_bytes(word,'little');assert value==mapping[key]
                over64+=value>=2**64;counts[key]+=1;n+=1
                stack[-2].remove(node);node.clear()
            if node.tag=='rr_nodes':break
            stack.pop()
        assert source.read(1)==b''
    assert counts==expected and n==v['nodes'] and max(mapping.values())==v['maximum_node_base']
    assert all(sha(p)==h for p,h in bindings.items())
    return dict(bindings=bindings,all_pass=True,nodes=n,scale=v['scale'],nodes_exceeding_u64=over64,
                independent_XML_float32_bits_and_payload_all_entries_equal=True,
                scope='Full original-node structural cost audit. Does not prove full routing search or native QoR.')

if __name__=='__main__':
    result=audit(sys.argv[1]);Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n')
    print('INDEPENDENT WIDE NODE AUDIT PASS',result['nodes'],result['nodes_exceeding_u64'],flush=True)
