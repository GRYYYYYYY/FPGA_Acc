"""Graph-specific indexed group mapping, exact float32 ceiling, fanout guard."""
import json,math,struct,sys,array,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def f32(t):return struct.unpack('<f',struct.pack('<f',float(t)))[0]
def main():
 root=R/'experiments/prospective_external_family_initialized_node_base_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);assert r['passed'] and r['exit_code']==0 and all(sha(p)==h for p,h in r['bindings'].items());protocol=read(root/'protocol.json');assert all(sha(p)==h for p,h in protocol['bindings'].items());ep=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19/endpoints.json';e=read(ep);graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256'] and protocol['command'][protocol['command'].index('--read_rr_graph')+1]==str(graph);table=root/'work/indexed.tsv';rows=[line.split() for line in table.read_text().splitlines()];assert rows[0]==['G','119878','8'];indices={int(t[1]):t for t in rows if t[0]=='I'};assert set(indices)==set(range(8));types={0:'SOURCE',1:'SINK',2:'IPIN',3:'OPIN',4:'CHANX',5:'CHANY'};group={};expected=Counter();details=[];scale=10**18
 for t in rows:
  if t[0]!='N':continue
  kind,idx,count=map(int,t[1:]);row=indices[idx];seg=int(row[2]);key=(types[kind],seg);assert key not in group and count>0;value=f32(row[3]);saved=f32(row[4]);quad=f32(row[7]);assert math.isfinite(value) and value>=0 and value==saved and quad==0.0;exact=Fraction(value);price=exact*scale;integer=(price.numerator+price.denominator-1)//price.denominator;assert price<=integer<price+1 and 0<=integer<2**64;group[key]=(idx,integer);expected[key]=count;details.append(dict(node_type=key[0],segment=seg,index=idx,nodes=count,base_cost_float32_text=row[3],base_bits=f'{int.from_bytes(struct.pack("<f",value),"little"):08x}',exact_numerator=exact.numerator,exact_denominator=exact.denominator,integer_base=integer,T_quadratic_zero=True))
 assert len(group)==8 and sum(expected.values())==119878;values=array.array('Q');counts=Counter();stack=[]
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   assert int(x.get('id'))==len(values);segment=x.find('segment');key=(x.get('type'),int(segment.get('segment_id')) if segment is not None else -1);assert key in group;values.append(group[key][1]);counts[key]+=1;parent.remove(x);x.clear()
  if x.tag=='rr_nodes':break
  stack.pop()
 assert counts==expected and len(values)==119878;target=root/'node_base.u64';target.write_bytes(values.tobytes());loaded=array.array('Q');loaded.frombytes(target.read_bytes());assert loaded==values;timing=R/'experiments/prospective_external_family_current_initial_timing_v1_2026-10-19/loader_contract_verification_v1.json';native_source=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/route/route_net.cpp';body=native_source.read_text();assert 'if (device_ctx.rr_indexed_data[RRIndexedDataId(index)].T_quadratic > 0.)' in body and 'saved_base_cost * factor' in body and 'factor = sqrt(fanout);' in body;assert not list((root/'work').glob('*.route'));paths=[rp,root/'protocol.json',table,ep,graph,target,timing,native_source,Path(__file__).resolve()]
 with (root/'verification.json').open('x') as f:json.dump(dict(status='ALL119878_GRAPH_NODE_BASE_GROUPS_FLOAT32_CEIL_AND_ZERO_QUADRATIC_FANOUT_GUARD_VERIFIED',nodes=len(values),scale=scale,array_byteorder=sys.byteorder,graph_sha256=e['graph_sha256'],timing_epoch_sha256=read(timing)['timing_epoch_sha256'],groups=details,all_native_base_equal_saved=True,all_native_T_quadratic_zero=True,ceil_error_less_than_one_lattice_unit=True,bindings={str(p):sha(p) for p in paths},scope='Native initialized type/index group counts uniquely map through indexed segment to every original XML type/segment; not a per-node native getter dump. Fanout update source preserves saved costs when T_quadratic0, applicable to this exact domain. SOURCE base remains native nonzero; prospective shared-NET objective must explicitly exclude structural root. Price lattice is a model scalar convention, not added native physical delay or timing closure.'),f,indent=2)
 print('EXTERNAL_NODE_BASE_DOMAIN_PASS',len(values),'groups',len(group),'prices',sorted(set(values)))
if __name__=='__main__':main()
