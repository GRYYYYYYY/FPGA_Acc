"""Architecture/packed/RR join for the reachable-pin trial's exact class."""
import json,re
import xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha,physical_maps,placements
protocol=json.loads(Path('experiments/frisc_graph_capture_2026-10-05/protocol.json').read_text())
paths={k:protocol['inputs'][k]['path'] for k in ('arch','net','place')}
paths['graph']='work/frisc_graph_capture_2026-10-05/rr_graph.xml'
paths['rows']='experiments/frisc_packed_pin_witness_2026-10-05/rows.json'

inputs={k:{'path':v,'sha256':sha(v)} for k,v in paths.items()}
for k in ('arch','net','place'):assert inputs[k]['sha256']==protocol['inputs'][k]['sha256']
types,grid,classes=physical_maps(paths['graph']);place=placements(paths['place'],inputs['net']['sha256'])
packed={b.attrib['name']:b for b in ET.parse(paths['net']).getroot().findall('block')}
arch={b.attrib['name']:b for b in ET.parse(paths['arch']).getroot().findall('./complexblocklist/pb_type')}
rows=json.loads(Path(paths['rows']).read_text())

checks=[]
for r in rows:
 pin=r['packed_sink'];block=packed[pin['block']];name=re.sub(r'\[\d+\]$','',block.attrib['instance'])
 port=arch[name].find(f"input[@name='{pin['port']}']")
 assert port is not None
 equivalence=port.attrib.get('equivalent','none');assert equivalence in {'full','none'}
 x,y,z,layer,_=place[pin['block']];tid,wo,ho=grid[x,y,layer];tile=types[tid]
 assert tile['name']==name and wo==ho==0
 members={ptc for (pb,sub,p,bit),(cid,kind,ptc) in tile['pins'].items() if pb==name and sub==z and p==pin['port'] and kind=='INPUT' and 0<=bit<int(port.attrib['num_pins'])}
 nominal=tile['pins'][name,z,pin['port'],pin['bit']];assert nominal[2]==pin['physical_pin_ptc']
 assert classes[x,y,layer,nominal[0],'SINK']==r['path_pin_witness']['sink_class']
 class_members={ptc for _,(cid,kind,ptc) in tile['pins'].items() if cid==nominal[0] and kind=='INPUT'}
 assert len(members)==int(port.attrib['num_pins'])
 if equivalence=='full':assert members==class_members
 else:assert class_members=={nominal[2]};members=class_members
 checks.append({'cid':r['connection_id'],'block':pin['block'],'pb_type':name,'port':pin['port'],'equivalent':equivalence,'sink_class':r['path_pin_witness']['sink_class'],'physical_members':sorted(members)})
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out=Path('experiments/frisc_full_pin_equivalence_audit_2026-10-05');out.mkdir()
(out/'source.py').write_text(Path(__file__).read_text())
receipt={'requests_verified':len(checks),'input_identities':inputs,'source_sha256':sha(out/'source.py'),'checks':checks,'scope':'architecture explicitly full input equivalence joined to packed block, placement and RR physical pin class; no executed packed-net remap, native legality or timing proof'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'requests_verified':len(checks),'full_equivalence_requests':sum(c['equivalent']=='full' for c in checks),'non_equivalent_requests':sum(c['equivalent']=='none' for c in checks)}))
