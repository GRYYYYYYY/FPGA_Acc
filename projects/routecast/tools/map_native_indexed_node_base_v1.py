"""Frozen float32-to-RC-lattice ceil mapping, complete original RR node domain."""
import json,struct,sys,xml.etree.ElementTree as E
from fractions import Fraction
from array import array
from collections import Counter
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_native_node_base_mapping_v1_2026-10-10';O.mkdir(exist_ok=False)
proof=R/'experiments/mmc_native_indexed_cost_dump_v1_2026-10-10/verification.json';v=json.loads(proof.read_text());assert v['all_904438_native_cost_index_type_segment_counts_match_original_XML'] and all(sha(p)==h for p,h in v['bindings'].items())
bindings={**v['bindings'],str(proof):sha(proof),str(Path(__file__).resolve()):sha(Path(__file__))}
protocol=R/'experiments/mmc_resident_manifest_scope_seed_handoff_v1_2026-10-10/model/protocol.json';p=json.loads(protocol.read_text());scale=p['price_unit_integer']*20*10**9;assert scale==10**18;bindings[str(protocol)]=sha(protocol)
table=R/'experiments/mmc_native_indexed_cost_dump_v1_2026-10-10/indexed.tsv';rows=[x.split() for x in table.read_text().splitlines()];indices={int(x[1]):x for x in rows if x[0]=='I'}
types={0:'SOURCE',1:'SINK',2:'IPIN',3:'OPIN',4:'CHANX',5:'CHANY'};mapping={};expected=Counter();details=[]
for x in rows:
 if x[0]!='N':continue
 kind,index,count=map(int,x[1:]);row=indices[index];key=(types[kind],int(row[2]));assert key not in mapping
 binary32=struct.unpack('f',struct.pack('f',float(row[3])))[0];exact=Fraction(binary32);assert exact>=0
 scaled=exact*scale;integer=(scaled.numerator+scaled.denominator-1)//scaled.denominator;assert 0<=integer<2**64 and 0<=integer-scaled<1
 mapping[key]=integer;expected[key]=count;details.append(dict(type=key[0],segment=key[1],index=index,float32_exact_numerator=exact.numerator,float32_exact_denominator=exact.denominator,integer_base=integer,ceil_error_numerator=(integer-scaled).numerator,ceil_error_denominator=(integer-scaled).denominator))
ep=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';endpoint=json.loads(ep.read_text());graph=Path(endpoint['inputs']['graph']['path']);assert sha(graph)==endpoint['graph_sha256'];bindings[str(ep)]=sha(ep);bindings[str(graph)]=sha(graph)
values=array('Q');counts=Counter();stack=[]
for event,el in E.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(el);continue
 if el.tag=='node':
  assert int(el.get('id'))==len(values);segment=el.find('segment');key=(el.get('type'),int(segment.get('segment_id')) if segment is not None else -1)
  assert key in mapping;values.append(mapping[key]);counts[key]+=1;stack[-2].remove(el);el.clear()
 if el.tag=='rr_nodes':break
 stack.pop()
assert counts==expected and len(values)==904438
output=O/'node_base.u64';output.write_bytes(values.tobytes());bindings[str(output)]=sha(output)
assert all(sha(p)==h for p,h in bindings.items())
(O/'verification.json').write_text(json.dumps(dict(bindings=bindings,scale=scale,nodes=len(values),array_byteorder=sys.byteorder,groups=details,all_original_node_ids_types_segments_and_native_group_counts_pass=True,ceil_error_less_than_one_RC_lattice_unit_per_entry=True,scope='Initialized native float32 base costs recovered from nine-digit table and ceiled into original RC scale. Unique type/segment indexed group mapping; no per-node native getter dump, dynamic fanout, criticality, live model, speed or causal evidence.'),indent=2)+'\n')
print('NATIVE NODE BASE MAPPING PASS',len(values),details,flush=True)
