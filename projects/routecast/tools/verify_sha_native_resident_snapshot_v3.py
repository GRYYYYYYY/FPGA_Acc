"""Full original XML/node/arc plus complete native NETpin inventory authentication."""
import json,struct,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_native_resident_snapshot_v3_2026-10-10';p=D/'receipt.json';v=json.loads(p.read_text());assert v['all_native_routes_byte_equal_original'] and all(sha(q)==h for q,h in v['bindings'].items());F=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/cold/demand/sha1';epfile=F/'endpoints.json';ep=json.loads(epfile.read_text());graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];nodes={};edges=Counter();nets={};pins={};header=footer=None;switches={};seen_switches=set()
for line in (D/'on/resident.tsv').read_text().splitlines():
 x=line.split('\t');kind=x[0]
 if kind=='H':assert header is None;header=list(map(int,x[1:]))
 elif kind=='N':
  n=int(x[1]);assert n not in nodes;nodes[n]=(tuple(map(int,x[2:9])),float.fromhex(x[9]),float.fromhex(x[10]))
 elif kind=='E':edges[tuple(map(int,x[1:]))]+=1
 elif kind=='S':
  sid=int(x[1]);assert sid not in switches;switches[sid]=(float.fromhex(x[2]),float.fromhex(x[3]))
 elif kind=='T':
  n=int(x[1]);assert n not in nets;nets[n]=(int(x[2]),int(x[3]),x[4])
 elif kind=='P':
  key=tuple(map(int,x[1:3]));assert key not in pins;pins[key]=int(x[3])
 elif kind=='F':assert footer is None;footer=list(map(int,x[1:]))
 else:raise AssertionError(kind)
assert header==[1,91088] and len(nodes)==91088 and footer==[sum(edges.values()),len(nets),len(pins)]
typemap={};seen=set();stack=[];arc_count=0
def f32(x):return struct.unpack('f',struct.pack('f',float(x)))[0]
for event,x in E.iterparse(graph,events=['start','end']):
 if event=='start':stack.append(x);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if x.tag=='node' and parent=='rr_nodes':
  n=int(x.get('id'));seen.add(n);values,r,c=nodes[n];kind=x.get('type');typemap.setdefault(kind,values[0]);assert typemap[kind]==values[0];loc=x.find('loc').attrib;expected=(int(x.get('capacity')),int(loc['xlow']),int(loc['xhigh']),int(loc['ylow']),int(loc['yhigh']),int(loc.get('layer','0')));assert values[1:]==expected;timing=x.find('timing');assert r==f32(timing.get('R')) and c==f32(timing.get('C'))
 if x.tag=='switch' and parent=='switches':
  sid=int(x.get('id'));seen_switches.add(sid);timing=x.find('timing');assert switches[sid]==(f32(timing.get('R','0')),f32(timing.get('Tdel','0')))
 if x.tag=='edge' and parent=='rr_edges':
  key=(int(x.get('src_node')),int(x.get('sink_node')),int(x.get('switch_id')));assert edges[key]>0;edges[key]-=1;arc_count+=1
 if x.tag in ['node','edge']:
  if len(stack)>1:stack[-2].remove(x)
  x.clear()
 stack.pop()
assert seen_switches==set(switches) and seen==set(nodes) and arc_count==801735 and not any(edges.values()) and len(typemap)==len(set(typemap.values()))==6
inventory={q['net_id']:q for q in map(json.loads,(F/'identity.jsonl').read_text().splitlines())};assert set(nets)==set(inventory)
for net,(ignored,count,name) in nets.items():
 q=inventory[net];assert ignored==int(q['ignored']) and name==q['name'] and count==len(q['pins']);assert {pin for n,pin in pins if n==net}==set(range(count))
required=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections']);observed=Counter((name,pins[net,0],pins[net,pin]) for net,(ignored,count,name) in nets.items() if not ignored and name in set(ep['net_names'].values()) for pin in range(1,count));assert observed==required and sum(required.values())==6273
bindings={str(q):sha(q) for q in [Path(__file__).resolve(),p,D/'on/resident.tsv',epfile,F/'identity.jsonl',graph]};assert all(sha(q)==h for q,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all91088_native_nodes_and801735_arc_multiset_equal_original_XML=True,all_native_NETnames_ignored_flags_and_pin_counts_equal=True,all6273_native_physical_SOURCE_SINK_pairs_equal=True,all_native_switch_R_Tdel_equal_original_XML_loaded_to_float=True,native_switches=len(switches),native_type_codes=typemap,native_nets=len(nets),native_pins=len(pins),scope='Complete in-memory snapshot topology and binary32 electrical values equal XML loaded-to-float values; NOT exact decimal Fraction RC predictor parity. All native pins including ignored/excluded retained. Unchanged route bytes certified; no zero-copy predictor/native gains.'),indent=2)+'\n');print('FULL NATIVE RESIDENT SNAPSHOT PASS',typemap,len(nets),len(pins))
