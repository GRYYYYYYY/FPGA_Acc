"""Resolve archived candidate critical arcs through packed wiring and RR sink classes."""
import json,re,hashlib,xml.etree.ElementTree as E
from pathlib import Path
p=Path('work/native_joint_budget_ex5p_STA_alignment_20261016/packed_cluster_mapping.json')
d=json.loads(p.read_text());packed=Path('work/native_sb_layer_capacity_scaling_20261015/layers3_cw80/circuit.net');place=packed.with_name('circuit.place');rr=packed.with_name('rr_graph.xml')
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
 def endpoint_matches(node):
  if not matches(node,component):return False
  ports=[po for section in ['inputs','outputs','clocks'] for po in node.findall(section+'/port') if po.get('name')==nextport]
  return len(ports)==1 and nextindex<len((ports[0].text or '').split())
 if parent is not None and parent.tag=='block' and endpoint_matches(parent):target=parent
 else:
  found=[b for b in block.findall('block') if endpoint_matches(b)]
  if not found and parent is not None:found=[b for b in parent.findall('block') if endpoint_matches(b)]
  assert len(found)==1,(block.attrib,token,[v.attrib for v in found]);target=found[0]
 return resolve(target,nextport,nextindex,trace,seen)

positions={}
for line in place.read_text().splitlines():
 f=line.split()
 if len(f)>=6 and f[1].isdigit():positions[f[0]]=(int(f[1]),int(f[2]),int(f[4]))
needed={int(t['sink']) for a in d['arcs'] for t in a['candidate_tasks']};nodes={};classes={}
for _,el in E.iterparse(rr,events=['end']):
 if el.tag=='block_type':
  if el.get('name')=='LAB':
   for i,c in enumerate(el.findall('pin_class')):
    for pin in c.findall('pin'):classes[pin.text]=i
  el.clear()
 elif el.tag=='node':
  n=int(el.get('id'))
  if n in needed:nodes[n]=dict(type=el.get('type'),loc={k:int(v) for k,v in el.find('loc').attrib.items() if k in ['xlow','ylow','layer','ptc']})
  el.clear()
 elif el.tag=='edge':el.clear()
assert set(nodes)==needed
rows=[]
for a in d['arcs']:
 if a['intracluster']:continue
 name,trace=resolve(atom(a['sink']),'in',a['physical_atom_input']);assert name==a['net'];last=trace[-1];assert last['instance']==a['sink_cluster']['instance']
 cls=classes['LAB.'+last['port']+'['+str(last['index'])+']'];pos=positions[a['sink_cluster']['name']]
 selected=[t for t in a['candidate_tasks'] if nodes[int(t['sink'])]['type']=='SINK' and tuple(nodes[int(t['sink'])]['loc'][k] for k in ['xlow','ylow','layer'])==pos and nodes[int(t['sink'])]['loc']['ptc']==cls];assert len(selected)==1,(a['net'],selected)
 rows.append(dict(net=a['net'],sink_atom=a['sink'],task=selected[0],packed_trace=trace,sink_class=cls,position=pos))
out=dict(status='five_intercluster_critical_arcs_bound_by_packed_wiring_placement_and_RR_sink_class',arcs=rows,source_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [p,packed,place,rr,Path(__file__)]},scope='Exact task selection by packed root input equivalence class and placement. No rerouting counterfactual or proof that repairing one arc closes global CPD.',research_complete=False)
with (p.parent/'RR_task_binding.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps([dict(net=a['net'],task=a['task']['id']) for a in rows]))
