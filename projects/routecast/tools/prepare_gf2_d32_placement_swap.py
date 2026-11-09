"""Prepare independent real placement endpoint changes, no native-router claim."""
import hashlib,json,re,shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from pre_route_endpoints import extract,placements,physical_maps,sha

out=Path('experiments/gf2_d32_placement_swap_2026-10-06')
if out.exists():raise ValueError('fresh output required')
prior=json.loads(Path('experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d32/endpoints.json').read_text())
inputs=prior['inputs']
for entry in inputs.values():
    if sha(entry['path'])!=entry['sha256']:raise ValueError('input changed')
net=Path(inputs['net']['path']);place=Path(inputs['place']['path']);graph=Path(inputs['graph']['path'])
rows=placements(place,inputs['net']['sha256']);types,grid,_=physical_maps(graph)
blocks=ET.parse(net).getroot().findall('block')
# Fixed deterministic first same-logical-type CLB pair; no metric-driven choice.
pair=[]
for block in blocks:
    name=block.attrib['name'];logical=re.sub(r'\[\d+\]$','',block.attrib['instance'])
    if logical!='clb':continue
    x,y,z,layer,_=rows[name]
    signature=(logical,z,layer,grid[(x,y,layer)][0])
    if not pair:first_signature=signature;pair=[name]
    elif signature==first_signature:pair.append(name);break
if len(pair)!=2:raise ValueError('no compatible pair')
out.mkdir(parents=True);(out/'source').mkdir()
for name in ('prepare_gf2_d32_placement_swap.py','pre_route_endpoints.py'):shutil.copyfile(Path(__file__).with_name(name),out/'source'/name)
protocol={'inputs':inputs,'pair':pair,'selection':'first two packed-order CLBs with same logical type, physical tile type, subtile and layer','scope':'real placement endpoint perturbation only; no native placement/routing legality run','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
lines=[]
for line in place.read_text().splitlines():
    fields=line.split()
    if fields and fields[0] in pair:
        name=fields[0];other=pair[1] if name==pair[0] else pair[0]
        x,y,z,layer,_=rows[other];bid=rows[name][4]
        line=f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{bid}'
    lines.append(line)
moved=out/'swapped.place';moved.write_text('\n'.join(lines)+'\n')
new,report=extract(net,moved,graph)
(out/'endpoints.json').write_text(json.dumps(new,indent=2)+'\n');(out/'mapping.json').write_text(json.dumps(report,indent=2)+'\n')
a={r['connection_id']:r for r in prior['connections']};b={r['connection_id']:r for r in new['connections']}
if set(a)!=set(b):raise AssertionError('connection identity changed')
if any(a[c]['net_id']!=b[c]['net_id'] for c in a):raise AssertionError('net identity changed')
changed=[c for c in a if a[c]!=b[c]];nets=sorted({a[c]['net_id'] for c in changed})
result={'protocol_sha256':sha(out/'protocol.json'),'swapped_place_sha256':sha(moved),'endpoint_sha256':sha(out/'endpoints.json'),'connections':len(a),'changed_connection_ids':changed,'affected_net_ids':nets,'affected_complete_net_connection_ids':[c for c in a if a[c]['net_id'] in nets],'identity_stable':True}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'pair':pair,'connections':len(a),'changed_connections':len(changed),'affected_nets':len(nets),'affected_complete_net_connections':len(result['affected_complete_net_connection_ids'])}))
