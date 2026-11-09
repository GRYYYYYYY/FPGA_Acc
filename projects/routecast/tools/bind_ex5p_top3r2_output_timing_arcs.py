"""Bind reported output arcs through BLIF/packed hierarchy/native pin identity."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_top3r2_output_bindings_2026-10-06';out.mkdir();diag=root/'experiments/ex5p_top3r2_timing_arcs_2026-10-06/receipt.json';d=json.loads(diag.read_text());epfile=root/'experiments/ex5p_placement_swap_2026-10-06/endpoints.json';ep=json.loads(epfile.read_text());mappingfile=epfile.parent/'mapping.json';mapping=json.loads(mappingfile.read_text());selectedfile=root/'experiments/ex5p_top3_joint_repair_2026-10-06/receipt.json';selected=json.loads(selectedfile.read_text());native=root/'experiments/ex5p_top3_joint_native_import_2026-10-06';nv=json.loads((native/'verification.json').read_text());assert nv['receipt_sha256']==sha(native/'receipt.json');bindings=json.loads((native/'pin_bindings.json').read_text());net=Path(ep['inputs']['net']['path']);blif=root/'work/nonzero_rc_ex5p_reference128_2026-10-06/design.blif';p={'inputs_sha256':{str(x):sha(x) for x in (diag,epfile,mappingfile,selectedfile,native/'pin_bindings.json',net,blif)},'policy':'Only direct namesoutput→outputpad arcs with same atomnet name; prove BLIF.names output, packed atomleaf within SOURCEcluster, outputpadSINK identity and endpoint/native binding. Other arcs unresolved.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');xml=ET.parse(net).getroot();blocks={b.get('name'):b for b in xml.findall('block')};blif_outputs=set()
for line in blif.read_text().splitlines():
 if line.startswith('.names '):blif_outputs.add(line.split()[-1])
queries={q['connection_id']:q for q in ep['connections']};records={q['connection_id']:q for q in selected['records']};details=mapping['pin_details'];targets=[path['steps'][-1] for path in d['predicted_top3_paths']]
results=[];unresolved=[]
for arc in targets:
 src=re.fullmatch(r'(.+)\.out\[0\] \(\.names\)',arc['from']);dst=re.fullmatch(r'out:(.+)\.outpad\[0\] \(\.output\)',arc['to'])
 if not src or not dst or src[1]!=dst[1]:unresolved.append(arc);continue
 name=src[1];assert name in blif_outputs
 sinks=[x for x in details if x['role']=='SINK' and x['net']==name and x['block']=='out:'+name and x['port']=='outpad' and x['bit']==0];sources=[x for x in details if x['role']=='SOURCE' and x['net']==name]
 assert len(sinks)==len(sources)==1;sink=sinks[0];source=sources[0]
 # Atom output must be physically nested in exactly the mapped packed driver cluster.
 leaves=[b for b in blocks[source['block']].iter('block') if b.get('name')==name and not b.findall('block') and any(name in (port.text or '').split() for port in b.findall('./outputs/port'))]
 assert len(leaves)==1
 matches=[q for q in queries.values() if q['net_id']==sink['net_id'] and q['source']==source['rr_node'] and q['sink']==sink['rr_node']];assert len(matches)==1;q=matches[0];rec=records[q['connection_id']];bind=bindings[str(q['connection_id'])];assert bind['packed_pin']==sink and bind['net_name']==name
 results.append({'timing_arc':arc,'connection_id':q['connection_id'],'net_id':q['net_id'],'net_name':name,'source_cluster':source['block'],'atom_instance':leaves[0].get('instance'),'source_rr':q['source'],'sink_rr':q['sink'],'native_net_id':bind['native_net_id'],'native_pin_index':bind['native_pin_index'],'physical_edge_ids':rec['answer']['physical_edge_ids'],'branch_delay_ns':rec['answer']['delay']*1e9/selected['scale']})
r={'bindings':results,'unresolved_arcs':unresolved,'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__)),'scope':'Exact external output atomNET/packedcluster/nativepad mapping, not mapping arbitrary LUT input timing arc or attributing complete report increment to RR delay. Development feedback targets only.'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print('bound',len(results),'unresolved',len(unresolved));print([(x['net_name'],x['connection_id'],x['branch_delay_ns']) for x in results])
