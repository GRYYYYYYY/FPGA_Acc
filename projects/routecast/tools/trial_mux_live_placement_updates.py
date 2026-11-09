"""Fixed first-compatible CLB swaps and live native-seeded mux predictions."""
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import extract,placements,physical_maps,sha
from native_place_serialization import canonical_place
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from staged_placement_reroute import stage_reroute_with_repair

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_live_placement_updates_2026-10-06';out.mkdir()
cases=[]
for width in (8,16,32):
    source=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{width}_c128'
    net,place,graph=(source/n for n in ('design.net','design.place','rr_graph.xml'))
    rows=placements(place,sha(net));types,grid,_=physical_maps(graph);pair=[];signature=None
    for block in ET.parse(net).getroot().findall('block'):
        name=block.get('name');logical=re.sub(r'\[\d+\]$','',block.get('instance'))
        if logical!='clb':continue
        x,y,z,layer,_=rows[name];sig=(logical,z,layer,grid[x,y,layer])
        if not pair:pair=[name];signature=sig
        elif sig==signature:pair.append(name);break
    assert len(pair)==2
    work=out/f'w{width}';work.mkdir();lines=[]
    for line in place.read_text().splitlines():
        fields=line.split()
        if fields and fields[0] in pair:
            name=fields[0];other=pair[1] if name==pair[0] else pair[0];x,y,z,layer,_=rows[other]
            line=f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{rows[name][4]}'
        lines.append(line)
    swapped=work/'swapped.place';swapped.write_text('\n'.join(lines)+'\n');swapped.write_text(canonical_place(swapped,net))
    cases.append(dict(width=width,source=str(source),pair=pair,swapped=str(swapped),inputs={str(p):sha(p) for p in (net,place,graph,source/'design.route')},swapped_sha256=sha(swapped)))
(out/'protocol.json').write_text(json.dumps(dict(cases=cases,source_sha256=sha(Path(__file__)),scope='Allthree compatible pair choices frozen before prediction. Same existing GF2 stage policy 1ns/10000/max4; no native moved-layout gate yet, retain failures.'),indent=2)+'\n')
results=[]
for case in cases:
    width=case['width'];source=Path(case['source']);work=out/f'w{width}'
    old,_=extract(source/'design.net',source/'design.place',source/'rr_graph.xml')
    new,_=extract(source/'design.net',case['swapped'],source/'rr_graph.xml')
    for label,data in (('original',old),('swapped',new)):(work/(label+'_endpoints.json')).write_text(json.dumps(data,indent=2)+'\n')
    ctx=PersistentRCContext(work/'original_endpoints.json');state=import_native_ledger(ctx,source/'design.route')
    update=stage_reroute_with_repair(state,work/'swapped_endpoints.json');candidate=update['repair'] or update['incremental']
    (work/'prediction.json').write_text(json.dumps(candidate,indent=2)+'\n')
    results.append(dict(width=width,completed=candidate['completed_connections'],failure=candidate['failure'],connections=len(old['connections']),prediction_sha256=sha(work/'prediction.json')))
    assert all(sha(p)==h for p,h in case['inputs'].items())
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=results),indent=2)+'\n');print(results[-1],flush=True)
