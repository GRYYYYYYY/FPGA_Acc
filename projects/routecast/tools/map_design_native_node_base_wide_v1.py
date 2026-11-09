"""Complete native group-to-original-node mapping, exact ceil to u128le payload."""
import json
import math
import struct
import sys
import xml.etree.ElementTree as E
from collections import Counter
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure

def map_nodes(endpoint_path,capture_directory,lattice_proof,output):
    endpoint_path=Path(endpoint_path).resolve();capture_directory=Path(capture_directory).resolve()
    lattice_proof=Path(lattice_proof).resolve();output=Path(output).resolve()
    endpoint=json.loads(endpoint_path.read_text());graph=Path(endpoint['inputs']['graph']['path'])
    proof=capture_directory/'criticality/verification.json';v=json.loads(proof.read_text())
    lattice=json.loads(lattice_proof.read_text());scale=lattice['exact_scale']
    assert v['nonignored_pin_keys_exactly_manifest'] and v['all_values_and_pin_identities_equal_v1']
    assert v['bindings'][str(endpoint_path)]==sha(endpoint_path)
    assert lattice['original_XML_all_node_and_edge_identities_and_electrical_values_pass']
    bindings={**closure([Path(__file__)]),str(endpoint_path):sha(endpoint_path)}
    for p,data in ((proof,v),(lattice_proof,lattice)):
        bindings[str(p)]=sha(p)
        for name,digest in data['bindings'].items():
            assert name not in bindings or bindings[name]==digest
            bindings[name]=digest
    assert bindings[str(graph)]==endpoint['graph_sha256']
    assert all(sha(p)==h for p,h in bindings.items())
    table=capture_directory/'indexed/indexed.tsv';assert bindings[str(table)]==sha(table)
    rows=[x.split() for x in table.read_text().splitlines()]
    assert rows[0][0]=='G' and int(rows[0][1])==lattice['nodes']
    indices={int(x[1]):x for x in rows if x[0]=='I'};assert len(indices)==int(rows[0][2])
    types=['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'];mapping={};expected=Counter();details=[]
    for row in rows:
        if row[0]!='N':continue
        kind,index,count=map(int,row[1:]);r=indices[index];key=(types[kind],int(r[2]))
        assert key not in mapping and count>0
        raw=struct.unpack('<f',struct.pack('<f',float(r[3])))[0]
        assert math.isfinite(raw) and raw>=0
        exact=Fraction(raw)*scale;integer=-(-exact.numerator//exact.denominator)
        assert 0<=integer<2**120 and 0<=integer-exact<1
        mapping[key]=integer;expected[key]=count
        details.append(dict(type=key[0],segment=key[1],index=index,count=count,integer_base=integer))
    output.mkdir(parents=True,exist_ok=False);path=output/'node_base.u128le'
    counts=Counter();stack=[];n=0
    with path.open('xb') as out:
        for event,node in E.iterparse(graph,events=('start','end')):
            if event=='start':stack.append(node);continue
            if node.tag=='node':
                assert node.get('id')==str(n);seg=node.find('segment')
                key=(node.get('type'),int(seg.get('segment_id')) if seg is not None else -1)
                value=mapping[key];out.write(struct.pack('<QQ',value%(2**64),value>>64))
                counts[key]+=1;n+=1;stack[-2].remove(node);node.clear()
            if node.tag=='rr_nodes':break
            stack.pop()
    assert counts==expected and n==lattice['nodes']
    assert path.stat().st_size==16*n
    bindings[str(path)]=sha(path)
    assert all(sha(p)==h for p,h in bindings.items())
    result=dict(bindings=bindings,nodes=n,scale=scale,payload_format='unsigned128_little_endian',
                payload_file=path.name,maximum_node_base=max(mapping.values()),groups=details,
                all_original_node_ids_types_segments_and_native_group_counts_pass=True,
                ceil_error_less_than_one_RC_lattice_unit_per_entry=True,
                scope='Every original RR node mapped from authenticated initialized native type/segment groups. Exact original float32 ceil policy; storage widened only. Requires independent bit/payload audit; no routing claim.')
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print('WIDE NODE MAPPING PASS',n,'max',result['maximum_node_base'],flush=True)

if __name__=='__main__':map_nodes(*sys.argv[1:])
