"""Second gate seeded from actual first winner, with native identity rebinding."""
import json
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha, placements
from audit_native_route import NODE
from native_place_serialization import canonical_place

ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/loaded_quality_gate_original_reload_2026-10-06'
assert json.loads((parent/'verification.json').read_text())['receipt_sha256']==sha(parent/'receipt.json')
out=ROOT/'experiments/loaded_quality_gate_reverse_2026-10-06';out.mkdir()
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
binary=ROOT/'build/loaded_native_quality_gate_v2_2026-10-06/gate_vpr'
identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
specs=[]
for width in (32,64,128):
    first=parent/f'gf2_d{width}_A'
    old=ROOT/f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}'
    raw=ROOT/f'work/gf2_certified_continuous_two_updates_2026-10-06/gf2_d{width}/1/work/gf2_d{width}_selected_reverse_native_import_2026-10-06/design.route'
    specs.append(dict(width=width,first=str(first),original=str(old),raw=str(raw),inputs={str(p):sha(p) for p in (*[first/n for n in ('design.blif','design.net','design.place','design.route')],raw,old/'design.place',old/'design.net',old/'rr_graph.xml')}))
(out/'protocol.json').write_text(json.dumps(dict(cases=specs,parent_receipt_sha256=sha(parent/'receipt.json'),binary_sha256=sha(binary),identity_sha256=sha(identity),source_sha256=sha(Path(__file__)),scope='Fresh second process seeded from accepted first canonical winner; archived reverse prediction paths rebound to current NET. Not same-process two-step or live estimator cost.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
def run(cmd,work,log,e):
    with log.open('w') as stream:return subprocess.run(cmd,cwd=work,env=e,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
rows=[]
for spec in specs:
    width=spec['width'];first=Path(spec['first']);old=Path(spec['original']);work=out/f'gf2_d{width}_A';work.mkdir();probe=work/'identity_probe';probe.mkdir()
    for name in ('design.blif','design.net','design.place'):shutil.copyfile(first/name,work/name)
    shutil.copyfile(first/'design.route',work/'seed.route')
    for name in ('design.blif','design.net'):shutil.copyfile(work/name,probe/name)
    oldpos=placements(old/'design.place',sha(old/'design.net'));current=placements(first/'design.place',sha(first/'design.net'))
    moved=[name for name in current if current[name][:4]!=oldpos[name][:4]];assert len(moved)==2
    pair=' '.join(str(current[name][4]) for name in moved)
    lines=[f'Netlist_File: design.net Netlist_ID: SHA256:{sha(probe/"design.net")}',first.joinpath('design.place').read_text().splitlines()[1],'']
    for block in ET.parse(probe/'design.net').getroot().findall('block'):
        name=block.get('name');x,y,z,layer,_=oldpos[name];lines.append(f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{current[name][4]}')
    (probe/'design.place').write_text('\n'.join(lines)+'\n');(probe/'design.place').write_text(canonical_place(probe/'design.place',probe/'design.net'))
    cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(old/'rr_graph.xml'),'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100']
    icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route')]='--analysis';icmd[icmd.index('--route_file')+1]='missing.route';table=probe/'identity.jsonl'
    assert run(icmd,probe,probe/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists()
    nets={r['name']:r for r in map(json.loads,table.read_text().splitlines())}
    xml=ET.parse(old/'rr_graph.xml').getroot();nodes={int(n.get('id')):n.find('loc').attrib for n in xml.find('rr_nodes')}
    sections={};record=None;head=[]
    for line in Path(spec['raw']).read_text().splitlines():
        m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
        if m:
            record=nets[m[1]];nid=record['net_id'];assert nid not in sections;sections[nid]=[f"Net {nid} ({record['name']})"];continue
        if record is None:head.append(line);continue
        m=NODE.match(line)
        if m and m[2]=='SINK':
            loc=nodes[int(m[1])];site=tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
            options=[p for p in record['pins'] if p['index']>0 and tuple(p[k] for k in ('x','y','layer','class'))==site];assert len(options)==1
            line=re.sub(r'Net_pin_index:\s*\d+',f"Net_pin_index: {options[0]['index']}",line)
        sections[nid].append(line)
    head[0]='Placement_File: candidate.place Placement_ID: SHA256:'+sha(probe/'design.place')
    for nid in sorted(sections):head.extend(sections[nid])
    (work/'predicted.route').write_text('\n'.join(head)+'\n')
    e={**env,'ROUTECAST_NATIVE_SEED':str(work/'seed.route'),'ROUTECAST_IMPORTED_CANDIDATE':str(work/'predicted.route'),'ROUTECAST_SAME_TARGET_GATE':'1','ROUTECAST_TIMING_RESTORE_PROBE':'1','ROUTECAST_MOVE_SEQUENCE':'A','ROUTECAST_MOVE_PAIRS':pair}
    code=run(cmd,work,work/'run.log',e);text=(work/'run.log').read_text();cpds=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)
    rows.append(dict(width=width,decision='A',exit_code=code,command=cmd,cpd_ns=float(cpds[-1]) if cpds else None,files={str(p):sha(p) for p in work.rglob('*') if p.is_file()}))
    assert all(sha(p)==h for p,h in spec['inputs'].items())
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(width,code,rows[-1]['cpd_ns'],flush=True)
