"""Trace logical critical LUT input pins through canonical packed hierarchy."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha,REF
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_critical_packed_pins_2026-10-06';out.mkdir();diag=root/'experiments/ex5p_swapped_timing_arcs_2026-10-06/receipt.json';d=json.loads(diag.read_text());net=root/'work/ex5p_swapped_canonical_reload_2026-10-06/0/reload/design.net';blif=root/'work/nonzero_rc_ex5p_reference128_2026-10-06/design.blif';p={'inputs_sha256':{str(x):sha(x) for x in (diag,net,blif)},'policy':'Worstpath LUT logical input index→unique port_rotation_map physical index→packed references→top input pin or internal atomdriver. Verify resolved logicalNET equals BLIF .names input token; ambiguity stops. Post-routing canonical NET, diagnostic only.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');xml=ET.parse(net).getroot();parents={c:b for b in xml.iter('block') for c in b.findall('block')};top=set(xml.findall('block'));leaves={}
for b in xml.iter('block'):
 if not b.findall('block') and b.get('name')!='open':leaves.setdefault(b.get('name'),[]).append(b)
atoms={}
for line in blif.read_text().splitlines():
 if line.startswith('.names '):tokens=line.split()[1:];assert tokens[-1] not in atoms;atoms[tokens[-1]]=tokens[:-1]
def porttokens(b,port):
 options=[x for section in ('inputs','outputs','clocks') for x in b.findall('./'+section+'/port') if x.get('name')==port];assert len(options)==1;return (options[0].text or '').split()
def trace(b,port,index,active=()):
 key=(b,port,index);assert key not in active;tokens=porttokens(b,port);assert 0<=index<len(tokens);token=tokens[index];step={'block':b.get('name'),'instance':b.get('instance'),'port':port,'physical_bit':index,'token':token}
 if '->' not in token:return token,[step]
 m=REF.fullmatch(token.split('->',1)[0]);assert m;instance,pname,pindex=m[1],m[2],int(m[3]);options=[c for c in b.findall('block') if c.get('instance')==instance]
 if not options:
  context=b
  while context is not None:
   own=context.get('instance');assert own
   if instance in (own,re.sub(r'\[\d+\]$','',own)):options=[context];break
   context=parents.get(context)
 assert len(options)==1;value,steps=trace(options[0],pname,pindex,active+(key,));return value,[step]+steps
rows=[]
for step in d['predicted_worst_path']['steps']:
 m=re.fullmatch(r'(.+)\.in\[(\d+)\] \(\.names\)',step['to'])
 if not m:continue
 name,index=m[1],int(m[2]);assert len(leaves.get(name,[]))==1;b=leaves[name][0];assert name in atoms and index<len(atoms[name]);rot=b.findall('./inputs/port_rotation_map[@name="in"]');assert len(rot)==1;mapping=(rot[0].text or '').split();physical=[i for i,x in enumerate(mapping) if x==str(index)];assert len(physical)==1;value,steps=trace(b,'in',physical[0]);assert value==atoms[name][index];boundary=[s for s in steps if any(t.get('instance')==s['instance'] and t.get('name')==s['block'] for t in top) and s['port']=='I'];rows.append({'timing_arc':step,'atom':name,'logical_bit':index,'physical_bit':physical[0],'resolved_net':value,'BLIF_input_matches':True,'packed_trace':steps,'external_cluster_input':boundary[-1] if boundary else None})
r={'bindings':rows,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Logical input rotation and packed reference provenance checked against BLIF. Rootpin is canonicalpostNET; mapping to original candidate RR branches requires nativephysicalpin/path identity, not assuming originalpackedbit stability.'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print([(x['atom'],x['logical_bit'],x['resolved_net'],x['external_cluster_input']) for x in rows])
