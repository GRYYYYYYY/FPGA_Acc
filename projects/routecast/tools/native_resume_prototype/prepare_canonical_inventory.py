"""Canonicalize a native output and reload with original VPR FULL/STA."""
import json,os,re,shutil,subprocess
from pathlib import Path
from audit_native_route import NODE
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2]
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
binary=shared/'build_tileplace_vpr/vpr/vpr'
identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
def run(cmd,work,log,environment):
    with log.open('w') as stream:return subprocess.run(cmd,cwd=work,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
def prepare_canonical(p,source,destination,inventory):
    assert all(sha(path)==h for path,h in p['files'].items())
    width,decision=p['width'],p['decision'];src=Path(source);work=Path(destination)
    graph=Path(p['command'][p['command'].index('--read_rr_graph')+1])
    inventory.validate(graph,inventory.digest);nodes={nid:loc for nid,(kind,loc) in inventory.nodes.items()};work.mkdir()
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
    inventory.validate(graph,inventory.digest)
    for name in ('report_timing.setup.rpt','report_timing.hold.rpt'):
        if (src/name).exists():shutil.copyfile(src/name,work/name)
    assert all(sha(path)==h for path,h in p['files'].items())
    return dict(command=cmd,pins=pins,graph_sha256=sha(graph),expected_cpd_ns=p['cpd_ns'],native_analysis_performed=False,files={str(f):sha(f) for f in work.iterdir() if f.is_file()})
