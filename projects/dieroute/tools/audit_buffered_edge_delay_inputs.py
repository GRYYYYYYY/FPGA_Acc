"""Independently check archived ex5p packed edge delays against buffered RC."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
graph=root/'work/native_ex5p_stratix2die_cw80_20261013/rr_graph.xml'
prefix=root/'work/rr_pair_ex5p_ordinary_schedule_bulk_v1_20261015/input'
r=ET.parse(graph).getroot()
switches={}
for s in r.findall('switches/switch'):
 assert s.attrib['type']=='mux'
 t=s.find('timing');a={} if t is None else t.attrib
 assert float(a.get('Cinternal','0'))==0
 switches[int(s.attrib['id'])]=(float(a.get('Tdel','0')),float(a.get('R','0')))
nodes={}
for n in r.findall('rr_nodes/node'):
 t=n.find('timing');assert t is not None
 nodes[int(n.attrib['id'])]=(float(t.attrib.get('R','0')),float(t.attrib.get('C','0')))
expected=defaultdict(list)
max_error=0.0
for e in r.findall('rr_edges/edge'):
 a=e.attrib;src,dst,sid=(int(a[k]) for k in ['src_node','sink_node','switch_id'])
 tdel,sr=switches[sid];nr,nc=nodes[dst]
 ps=(tdel+(sr+0.5*nr)*nc)*1e12
 assert 0<=ps<=65535
 q=round(ps);max_error=max(max_error,abs(q-ps))
 expected[src].append((dst,q))
packed=list(struct.iter_unpack('<IHH',prefix.with_suffix('.edges').read_bytes()))
node_records=list(struct.iter_unpack('<IHH',prefix.with_suffix('.nodes').read_bytes()))
assert len(node_records)==len(nodes)
checked=0
for src,(begin,count,reserved) in enumerate(node_records):
 actual=sorted((dst,delay) for dst,base,delay in packed[begin:begin+count])
 assert actual==sorted(expected[src]),src
 checked+=count
assert checked==len(packed)==sum(map(len,expected.values()))
paths=[graph,prefix.with_suffix('.edges'),prefix.with_suffix('.nodes'),Path(__file__).resolve(),root/'../persistroute/tools/pack_hls_inputs.py']
# Source converter is linked separately below; packed artifacts are authoritative.
paths[-1]=root.parent/'persistroute/tools/pack_hls_inputs.py'
sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
out=root/'work/ex5p_buffered_edge_delay_audit_20261015';out.mkdir(exist_ok=False)
(out/'audit.json').write_text(json.dumps(dict(status='all_ex5p_packed_edge_delays_match_buffered_rc_formula',checked_edges=checked,switches=len(switches),maximum_rounding_error_ps=max_error,source_sha256=sources,
 scope='Every CSR edge delay multiset checked per source against archived XML buffered local RC with zero Cinternal. Python double and integer-ps rounding, not bit-exact VPR float arithmetic, complete route-tree RC equivalence or QoR validation.',board_result=False,research_complete=False),indent=2)+'\n')
print(checked,max_error)
