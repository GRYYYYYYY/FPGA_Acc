import json,time,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha,extract,placements,physical_maps
root=Path(__file__).resolve().parents[1];features_path=root/'experiments/native_baseline_critical_geometry_2026-10-06/features.json';features=json.loads(features_path.read_text());assert all(sha(p)==h for p,h in features['inputs_sha256'].items());source=root/'work/adder_tree_family_native_capture_v2_2026-10-06/adder_tree_2L_032bits';graph=source/'rr_graph.xml';out=root/'experiments/native_baseline_critical_rr_pin_2026-10-06';out.mkdir();start=time.perf_counter();endpoints,report=extract(source/'design.net',source/'design.place',graph);types,grid,rr=physical_maps(graph);place=placements(source/'design.place',sha(source/'design.net'));loc={v[4]:(v[0],v[1],v[3]) for v in place.values()};resolved=[];unknown=[]
tree=ET.parse(source/'design.net').getroot();parents={c:p for p in tree.iter('block') for c in p.findall('block')};roots=set(tree.findall('block'))
text=(source/'report_timing.setup.rpt').read_text().split('#Path 1\n',1)[1].split('data arrival time',1)[0];sink_pins={}
for line in text.splitlines():
 m=re.match(r'^(.*?)\.(in|D)\[(\d+)\]\s+',line)
 if m:assert m[1] not in sink_pins;sink_pins[m[1]]=(m[2],int(m[3]))
def trace(atom,port,bit):
 matches=[b for b in tree.iter('block') if b.get('name')==atom and not b.findall('block')];assert len(matches)==1;b=matches[0]
 rotation=b.find(f"inputs/port_rotation_map[@name='{port}']")
 if rotation is not None:
  bits=(rotation.text or '').split();indices=[i for i,x in enumerate(bits) if x==str(bit)];assert len(indices)==1;bit=indices[0]
 seen=set();path=[]
 while True:
  assert (b,port,bit) not in seen;seen.add((b,port,bit));ports=[p for kind in ('inputs','outputs','clocks') for p in b.findall(kind+'/port') if p.get('name')==port];assert len(ports)==1;token=(ports[0].text or '').split()[bit];path.append({'instance':b.get('instance'),'port':port,'bit':bit,'token':token})
  if b in roots:assert '->' not in token and token!='open';return b.get('name'),port,bit,token,path
  assert '->' in token;ref=token.split('->',1)[0];m=re.fullmatch(r'([^.]*)\.([^.[\]]+)\[(\d+)\]',ref);assert m;instance,port,bit=m[1],m[2],int(m[3]);context=b;found=None
  while context is not None:
   own=context.get('instance','')
   if instance in (own,re.sub(r'\[\d+\]$','',own)):found=context;break
   children=[c for c in context.findall('block') if c.get('instance')==instance]
   if children:assert len(children)==1;found=children[0];break
   context=parents.get(context)
  assert found is not None;b=found

for i,edge in enumerate(features['connections']):
 net=edge['source_atom'];sink_port,sink_bit=sink_pins[edge['sink_atom']];root_name,root_port,root_bit,root_net,pin_trace=trace(edge['sink_atom'],sink_port,sink_bit);assert root_net==net;src=[p for p in report['pin_details'] if p['net']==net and p['role']=='SOURCE' and p['block_id']==edge['source_block']];sinks=[p for p in report['pin_details'] if p['net']==net and p['role']=='SINK' and p['block_id']==edge['sink_block'] and p['port']==root_port and p['bit']==root_bit]
 if len(src)!=1 or len({p['rr_node'] for p in sinks})!=1:
  unknown.append({'edge':i,'reason':'source atom net identity or sink class not uniquely resolved','source_matches':len(src),'sink_classes':len({p['rr_node'] for p in sinks})});continue
 s=src[0];t=sinks[0];assert any(c['source']==s['rr_node'] and c['sink']==t['rr_node'] for c in endpoints['connections']);resolved.append({'edge':i,'net_name':net,'source':s,'sink_class':t,'equivalent_sink_pins':len(sinks),'baseline_edge_ns':edge['baseline_edge_ns'],'canonical_sink_pin_trace':pin_trace,'atom_sink_port':sink_port,'atom_sink_bit':sink_bit})
queries=[]
for feature in features['pairs']:
 a,b=feature['pair'];moved=loc.copy();moved[a],moved[b]=moved[b],moved[a]
 for edge in resolved:
  refs=[]
  for kind,pin in [('SOURCE',edge['source']),('SINK',edge['sink_class'])]:
   x,y,layer=moved[pin['block_id']];x0,y0,l0=loc[pin['block_id']];assert grid[(x,y,layer)]==grid[(x0,y0,l0)],'heterogeneous sites unsupported';key=(x,y,layer,pin['class_id'],kind);assert key in rr;refs.append(rr[key])
  queries.append({'pair_index':feature['index'],'edge':edge['edge'],'net_name':edge['net_name'],'source':refs[0],'sink':refs[1],'baseline_source':edge['source']['rr_node'],'baseline_sink':edge['sink_class']['rr_node']})
result={'resolved':resolved,'unknown':unknown,'candidate_queries':queries,'wall_s':time.perf_counter()-start,'inputs_sha256':{str(p):sha(p) for p in (features_path,source/'design.net',source/'design.place',graph)},'scope':'RR class-level mapping from packed net and prior baseline critical atom identities; equivalent sink pins may share class. Pre-route net IDs are not native NET IDs. Same physical tile type only, no exact atom pin, native delay budget or candidate results assumed.'};(out/'queries.json').write_text(json.dumps(result,indent=2)+'\n');print('resolved',len(resolved),'unknown',len(unknown),'queries',len(queries))
