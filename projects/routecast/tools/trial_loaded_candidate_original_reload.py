"""Canonicalize six loaded-import outputs, then original VPR FULL/STA reload."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET
from audit_native_route import NODE
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/native_loaded_candidate_import_gf2_2026-10-06'
pr=json.loads((parent/'receipt.json').read_text())
assert json.loads((parent/'verification.json').read_text())['receipt_sha256']==sha(parent/'receipt.json')
out=ROOT/'experiments/loaded_candidate_original_reload_2026-10-06';out.mkdir()
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
binary=shared/'build_tileplace_vpr/vpr/vpr'
identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
assert sha(binary)=='a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc'
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(parent/'receipt.json'),binary_sha256=sha(binary),identity_binary_sha256=sha(identity),source_sha256=sha(Path(__file__)),scope='Post-sync native NET identity remap, unique site/class pin mapping; six fresh original FULL/STA reloads. No timing benefit.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
def run(cmd,work,log,environment):
    with log.open('w') as stream:return subprocess.run(cmd,cwd=work,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
rows=[]
for p in pr['rows']:
    assert all(sha(path)==h for path,h in p['files'].items())
    width,decision=p['width'],p['decision'];src=parent/f'gf2_d{width}_{decision}';work=out/f'gf2_d{width}_{decision}';work.mkdir()
    graph=Path(p['command'][p['command'].index('--read_rr_graph')+1])
    xml=ET.parse(graph).getroot();nodes={int(n.get('id')):n.find('loc').attrib for n in xml.find('rr_nodes')}
    shutil.copyfile(src/'design.blif',work/'design.blif');shutil.copyfile(src/'design.net.post_routing',work/'design.net')
    place=src/('accepted.place' if decision=='A' else 'design.place')
    text=re.sub(r'Netlist_ID:\s*\S+','Netlist_ID: SHA256:'+sha(work/'design.net'),place.read_text(),count=1)
    (work/'design.place').write_text(text)
    cmd=p['command'].copy();cmd[0]=str(binary);cmd[cmd.index('--route')]='--analysis';cmd[cmd.index('--route_file')+1]='design.route'
    icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route_file')+1]='missing.route'
    table=work/'identity.jsonl'
    assert run(icmd,work,work/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists()
    nets={row['name']:row for row in map(json.loads,table.read_text().splitlines())}
    sections={};head=[];record=None;pins=0
    for line in (src/'output.route').read_text().splitlines():
        m=re.match(r'^Net\s+(\d+)\s+\((.*?)\)',line)
        if m:
            record=nets[m[2]];nid=record['net_id'];assert nid not in sections
            sections[nid]=[re.sub(r'^Net\s+\d+',f'Net {nid}',line)];continue
        if record is None:head.append(line);continue
        m=NODE.match(line)
        if m and m[2]=='SINK':
            loc=nodes[int(m[1])];site=tuple(int(loc.get(k,'0')) for k in ('xlow','ylow','layer','ptc'))
            options=[pin for pin in record['pins'] if pin['index']>0 and tuple(pin[k] for k in ('x','y','layer','class'))==site]
            assert len(options)==1,'ambiguous canonical SINK identity'
            line=re.sub(r'Net_pin_index:\s*\d+',f"Net_pin_index: {options[0]['index']}",line);pins+=1
        sections[nid].append(line)
    head[0]='Placement_File: design.place Placement_ID: SHA256:'+sha(work/'design.place')
    lines=head[:]
    for nid in sorted(sections):lines.extend(sections[nid])
    (work/'design.route').write_text('\n'.join(lines)+'\n')
    code=run(cmd,work,work/'reload.log',env);log=(work/'reload.log').read_text()
    cpd=re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)
    mis=re.search(r'Found (\d+) mismatches',log);fix=re.search(r'Fixed (\d+) routing traces',log)
    row=dict(width=width,decision=decision,command=cmd,exit_code=code,cpd_ns=float(cpd[1]) if cpd else None,expected_cpd_ns=p['cpd_ns'],mismatches=int(mis[1]) if mis else None,fixups=int(fix[1]) if fix else None,pins=pins,graph_sha256=sha(graph),files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
    rows.append(row);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
    print(width,decision,code,row['cpd_ns'],row['mismatches'],row['fixups'],flush=True)
assert all(sha(path)==h for p in pr['rows'] for path,h in p['files'].items())
