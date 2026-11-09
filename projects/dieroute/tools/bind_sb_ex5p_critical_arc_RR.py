"""Bind the observed printed arc through packed pins, placement and real RR trees."""
import collections,csv,hashlib,json,re,struct,xml.etree.ElementTree as E
from decimal import Decimal
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/'work/sb_ex5p_native_STA_path_alignment_20261015';P=R/'work/sb_ex5p_critical_arc_RR_binding_20261015'
def main():
 P.mkdir(exist_ok=False);refs={}
 def sha(f):
  key=str(f)
  if key not in refs:
   h=hashlib.sha256()
   with Path(f).open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 prior=json.loads((A/'independent_audit.json').read_text());protocol=json.loads((A/'protocol.json').read_text())
 for f,h in prior['source_sha256'].items():assert sha(f)==h,f
 native=R/'work/native_sb_layer_capacity_scaling_20261015/layers3_cw80';packed=native/'circuit.net';place=native/'circuit.place';blif=native/'circuit.blif';rr=native/'rr_graph.xml'
 root=E.parse(packed).getroot();parents={child:node for node in root.iter() for child in node}
 def atom(name):
  found=[b for b in root.iter('block') if b.get('name')==name and not b.findall('block') and b.find('outputs/port') is not None];assert len(found)==1;return found[0]
 def chain(node):
  out=[]
  while node is not root:out.append(node);node=parents[node]
  return out
 def port(block,name):
  found=[p for section in ['inputs','outputs','clocks'] for p in block.findall(section+'/port') if p.get('name')==name];assert len(found)==1,(block.attrib,name);return (found[0].text or '').split()
 def matches(block,reference):
  actual=block.get('instance','');return actual==reference or ('[' not in reference and re.sub(r'\[\d+\]$','',actual)==reference)
 def resolve(block,name,index,trace=None,seen=None):
  trace=[] if trace is None else trace;seen=set() if seen is None else seen;key=(id(block),name,index);assert key not in seen;seen.add(key);tokens=port(block,name);assert index<len(tokens);token=tokens[index];trace.append(dict(block=block.get('name'),instance=block.get('instance'),port=name,index=index,value=token))
  if token=='open':return None,trace
  if '->' not in token:return token,trace
  m=re.fullmatch(r'([^\.]+)\.([^\[]+)\[(\d+)\]',token.split('->')[0]);assert m,token;component,nextport,nextindex=m[1],m[2],int(m[3]);parent=parents.get(block)
  if parent is not None and parent.tag=='block' and matches(parent,component):target=parent
  else:
   found=[b for b in block.findall('block') if matches(b,component)]
   if not found and parent is not None:found=[b for b in parent.findall('block') if matches(b,component)]
   assert len(found)==1,(block.attrib,token,[v.attrib for v in found]);target=found[0]
  return resolve(target,nextport,nextindex,trace,seen)
 source=atom('[3355]');sink=atom('[3663]');source_cluster=chain(source)[-1];sink_cluster=chain(sink)[-1];assert port(source,'out')==['[3355]']
 definition=[line.split()[1:] for line in blif.read_text().splitlines() if line.startswith('.names ') and line.split()[-1]=='[3663]'];assert len(definition)==1 and definition[0][1]=='[3355]'
 rotation=sink.find("inputs/port_rotation_map[@name='in']");assert rotation is not None;physical=[i for i,v in enumerate(rotation.text.split()) if v=='1'];assert len(physical)==1
 net_name,sink_trace=resolve(sink,'in',physical[0]);assert net_name=='[3355]';assert sink_trace[-1]['instance']==sink_cluster.get('instance');sink_port=sink_trace[-1]['port'];sink_port_index=sink_trace[-1]['index']
 driver_ports=[]
 for po in source_cluster.findall('outputs/port'):
  for i in range(len((po.text or '').split())):
   name,trace=resolve(source_cluster,po.get('name'),i)
   if name==net_name:driver_ports.append(dict(port=po.get('name'),index=i,trace=trace))
 assert len(driver_ports)==1
 placements={}
 for line in place.read_text().splitlines():
  if not line or line.startswith(('#','Netlist_File:','Array size:')):continue
  fields=line.split()
  if len(fields)>=6 and fields[1].isdigit():placements[fields[0]]=dict(x=int(fields[1]),y=int(fields[2]),subblock=int(fields[3]),layer=int(fields[4]),block=int(fields[5].lstrip('#')))
 src_pos=placements[source_cluster.get('name')];dst_pos=placements[sink_cluster.get('name')]
 connections=R/'work/sb_native_roundtrip_preflight_20261015/layers3_cw80/connections.csv';rows=[v for v in csv.DictReader(connections.open()) if v['net']==net_name];assert rows and {int(v['net_id']) for v in rows}=={138};source_rr={int(v['source']) for v in rows};assert len(source_rr)==1;source_rr=source_rr.pop()
 def tree(path):
  inside=False;seen=set();parent={};switch={};kind={};pins={};previous=None;previous_switch=None
  for line in path.read_text().splitlines():
   m=re.match(r'^Net\s+(\d+)\s+\((.*)\)',line)
   if m:
    if inside:break
    inside=int(m[1])==138
    if inside:assert m[2]==net_name
    continue
   if not inside:continue
   m=re.match(r'^Node:\s*(\d+)\s+(SOURCE|SINK|IPIN|OPIN|CHANX|CHANY)\b',line)
   if not m:continue
   node=int(m[1]);kind[node]=m[2];sw=int(re.search(r'Switch:\s*(-?\d+)',line)[1])
   if node not in seen:
    if previous is not None:assert kind[previous]!='SINK';parent[node]=previous;switch[node]=previous_switch
    else:assert node==source_rr and kind[node]=='SOURCE'
    seen.add(node)
   if kind[node]=='SINK':pins[node]=int(re.search(r'Net_pin_index:\s*(\d+)',line)[1])
   previous=node;previous_switch=sw
  assert seen and len(parent)==len(seen)-1;return dict(nodes=seen,parent=parent,switch=switch,kind=kind,pins=pins)
 trees={c['label']:tree(Path(c['route'])) for c in protocol['cases']};needed=set().union(*(t['nodes'] for t in trees.values()),{int(v['sink']) for v in rows});nodes={};switches={};pin_classes={};triples=collections.Counter();wanted_triples={(a,b,t['switch'][b]) for t in trees.values() for b,a in t['parent'].items()}
 for _,el in E.iterparse(rr,events=['end']):
  if el.tag=='block_type':
   if el.get('name')=='LAB':
    for ci,c in enumerate(el.findall('pin_class')):
     for pin in c.findall('pin'):pin_classes[pin.text]=dict(class_id=ci,type=c.get('type'),ptc=int(pin.get('ptc')),class_pins=len(c.findall('pin')))
   el.clear()
  elif el.tag=='switch':
   timing=el.find('timing');switches[int(el.get('id'))]=dict(attributes=dict(el.attrib),timing=dict(timing.attrib));el.clear()
  elif el.tag=='node':
   n=int(el.get('id'))
   if n in needed:nodes[n]=dict(type=el.get('type'),direction=el.get('direction'),loc={k:int(v) for k,v in el.find('loc').attrib.items()},timing=dict(el.find('timing').attrib))
   el.clear()
  elif el.tag=='edge':
   key=(int(el.get('src_node')),int(el.get('sink_node')),int(el.get('switch_id')))
   if key in wanted_triples:triples[key]+=1
   el.clear()
 assert set(nodes)==needed and all(triples[v]>0 for v in wanted_triples)
 source_pin=pin_classes['LAB.'+driver_ports[0]['port']+'['+str(driver_ports[0]['index'])+']'];target_pin=pin_classes['LAB.'+sink_port+'['+str(sink_port_index)+']']
 assert nodes[source_rr]['type']=='SOURCE' and nodes[source_rr]['loc']['ptc']==source_pin['class_id']
 def at(node,position):return all(nodes[node]['loc'][k]==position[v] for k,v in [('xlow','x'),('ylow','y'),('layer','layer')])
 assert at(source_rr,src_pos);selected=[v for v in rows if at(int(v['sink']),dst_pos) and nodes[int(v['sink'])]['loc']['ptc']==target_pin['class_id']];assert len(selected)==1;task=selected[0];sink_rr=int(task['sink']);assert int(task['id'])==895 and sink_rr==14256
 precision=R/'work/rr_remaining_tail_precision_development_v2_20261015';inputs=json.loads((precision/'protocol.json').read_text());case=next(v for v in inputs['cases'] if v['label']=='ex5p');tasks=Path(case['input_prefix']+'.tasks');raw=struct.unpack_from('<IIIIHHIII',tasks.read_bytes(),int(task['id'])*32);assert raw[:4]==tuple(int(task[k]) for k in ['id','net_id','source','sink'])
 outcomes=[]
 for c in protocol['cases']:
  label=c['label'];t=trees[label];path=[sink_rr]
  while path[-1]!=source_rr:assert len(path)<=len(t['nodes']);path.append(t['parent'][path[-1]])
  path.reverse();assert t['pins'][sink_rr]==4
  csvpath=R/'work/sb_native_roundtrip_preflight_20261015/layers3_cw80/native_tree.csv' if label=='baseline' else Path(c['route']).parent.parent/'route.route_trees.csv'
  exported=[v for v in csv.DictReader(csvpath.open()) if int(v['net_id'])==138];assert {(int(v['parent']),int(v['child'])) for v in exported}=={(a,b) for b,a in t['parent'].items()}
  if label=='baseline':assert all(int(v['switch_id'])==t['switch'][int(v['child'])] for v in exported)
  last=nodes[path[-2]];assert last['type']=='IPIN' and at(path[-2],dst_pos);physical_pin=next(v for v in pin_classes.values() if v['ptc']==last['loc']['ptc']);assert physical_pin['class_id']==target_pin['class_id']
  length=sum(1+n['loc']['xhigh']-n['loc']['xlow']+n['loc']['yhigh']-n['loc']['ylow'] for n in (nodes[i] for i in path) if n['type'] in ['CHANX','CHANY'] and n['direction']!='NONE')
  crossings=sum(nodes[a]['loc']['layer']!=nodes[b]['loc']['layer'] for a,b in zip(path,path[1:]));edge_rows=[];tdel=Decimal(0)
  for a,b in zip(path,path[1:]):
   sw=t['switch'][b];value=Decimal(switches[sw]['timing']['Tdel'])*Decimal(10**9);tdel+=value;edge_rows.append(dict(source=a,target=b,switch_id=sw,switch_Tdel_ns=str(value),matching_RR_edge_records=triples[a,b,sw]))
  sta=next(v for v in prior['paths'][label] if v['endpoint']=='out:o_56_.outpad[0]');arc=next(v for v in sta['arcs'] if v['source']=='[3355].out[0] (.names)' and v['target']=='[3663].in[1] (.names)')
  node_rc_zero=all(all(k in nodes[n]['timing'] and Decimal(nodes[n]['timing'][k])==0 for k in ['R','C']) for n in t['nodes']);switch_rc_zero=all(all(k in switches[v]['timing'] and Decimal(switches[v]['timing'][k])==0 for k in ['R','Cin','Cout']) for v in set(t['switch'].values()))
  outcomes.append(dict(case=label,net_id=138,task_id=895,source_rr=source_rr,sink_rr=sink_rr,net_pin_index=4,path=path,edges=edge_rows,path_nodes=len(path),native_channel_length_units=length,modeled_layer_crossings=crossings,actual_IPIN=path[-2],actual_IPIN_ptc=last['loc']['ptc'],static_packed_input_ptc=target_pin['ptc'],same_input_equivalence_class=True,switch_Tdel_sum_ns=str(tdel),printed_STA_arc_ns=arc['increment_ns'],printed_arc_minus_switch_Tdel_sum_ns=str(Decimal(arc['increment_ns'])-tdel),whole_net_nodes_R_C_zero=node_rc_zero,whole_net_switch_R_Cin_Cout_zero=switch_rc_zero))
  sha(csvpath);sha(Path(c['route']))
 for f in [A/'independent_audit.json',A/'protocol.json',packed,place,blif,rr,connections,tasks,precision/'protocol.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='printed_3355_to3663_arc_bound_to_native_net138_task895_RRpaths',logical_connection=dict(source_atom='[3355]',source_pin='out[0]',sink_atom='[3663]',sink_logical_pin='in[1]',sink_physical_atom_pin=physical[0],net=net_name,net_id=138,task_id=895,source_cluster=dict(name=source_cluster.get('name'),instance=source_cluster.get('instance'),place=src_pos,root_output=driver_ports[0]),sink_cluster=dict(name=sink_cluster.get('name'),instance=sink_cluster.get('instance'),place=dst_pos,static_root_input_port=sink_port,static_root_input_index=sink_port_index),packed_input_trace=sink_trace,input_equivalence_class=target_pin),outcomes=outcomes,RR_nodes=nodes,RR_switches=switches,source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Static BLIF logical pin, packed rotation/wiring, fixed placement, native route Net_pin_index4 and SINK class bind one observed printed arc to task895. Actual physical IPIN may differ from static packed pin because class has equivalent inputs. All net138 node/switch edges exist in RR XML; full node-tree sets match original/C-model CSV. Switch-only Tdel sums are not asserted to equal complete connection delay; R/C and residuals retained. SB3 modeled path observations only, no physical SLL/U280 timing, single-net counterfactual or quality adoption.')
 with (P/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps({k:[{n:v for n,v in row.items() if n not in ['path','edges']} for row in outcomes] for k in ['outcomes']}))
if __name__=='__main__':main()
