"""Fresh full-family identity probes and unique-site/class contract audit."""
import json
import os
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_native_identity_contract_2026-10-06';out.mkdir()
binary=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
specs=[]
for width in (8,16,32):
    source=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{width}_c128'
    specs.append(dict(width=width,source=str(source),inputs={str(source/n):sha(source/n) for n in ('design.blif','design.net','design.place','rr_graph.xml')}))
(out/'protocol.json').write_text(json.dumps(dict(cases=specs,binary_sha256=sha(binary),architecture_sha256=sha(arch),source_sha256=sha(Path(__file__)),scope='Fresh identity-only probes at frozen mux channel128 layouts. Ambiguity audit, not move/native quality or generalization success.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};rows=[]
for spec in specs:
    work=out/f"w{spec['width']}";work.mkdir();source=Path(spec['source'])
    for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/name,work/name)
    cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','missing.route','--read_rr_graph',str(source/'rr_graph.xml'),'--route_chan_width','128','--num_workers','1','--check_route','full']
    table=work/'identity.jsonl'
    with (work/'identity.log').open('w') as stream:code=subprocess.run(cmd,cwd=work,env={**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)},stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
    assert code==1 and table.exists()
    records=[json.loads(line) for line in table.read_text().splitlines()];ambiguous=[];pins=0
    for record in records:
        sites=defaultdict(list)
        for pin in record['pins']:
            if pin['index']>0:sites[tuple(pin[k] for k in ('x','y','layer','class'))].append(pin);pins+=1
        for site,options in sites.items():
            if len(options)>1:ambiguous.append(dict(net=record['name'],site=site,pins=options))
    (work/'ambiguous.json').write_text(json.dumps(ambiguous,indent=2)+'\n')
    assert all(sha(p)==h for p,h in spec['inputs'].items())
    rows.append(dict(width=spec['width'],exit_code=code,command=cmd,nets=len(records),sink_pins=pins,ambiguous_site_classes=len(ambiguous),affected_nets=len({a['net'] for a in ambiguous}),files={str(p):sha(p) for p in work.iterdir() if p.is_file()}))
    print(spec['width'],'ambiguous',len(ambiguous),'sinks',pins,flush=True)
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
