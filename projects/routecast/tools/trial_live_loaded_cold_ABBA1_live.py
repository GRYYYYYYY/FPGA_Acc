"""Prospective live two-update lifecycle with canonical native handoff."""
import json
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import placements,sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from staged_placement_reroute import stage_reroute_with_repair
from serialize_live_native_candidate import serialize
from native_place_serialization import canonical_place
from loaded_native_canonical_reload import canonical_reload
from stream_native_route_audit import audit

ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/live_loaded_cold_ABBA1_live_2026-10-06';out.mkdir()
binary=ROOT/'build/loaded_native_quality_gate_v2_2026-10-06/gate_vpr'
identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'
arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
cases=[]
for width in (32,64,128):
    initial=ROOT/f'work/gf2_recurrence_native_reference_2026-10-06/gf2_d{width}'
    original=ROOT/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{width}/endpoints.json'
    swapped=ROOT/f'experiments/gf2_d{width}_placement_swap_2026-10-06/endpoints.json'
    files=[*(initial/n for n in ('design.blif','design.net','design.place','design.route')),original,swapped]
    cases.append(dict(width=width,initial=str(initial),original=str(original),targets=[str(swapped),str(original)],inputs={str(p):sha(p) for p in files}))
sources=[Path(__file__),*[ROOT/'tools'/n for n in ('serialize_live_native_candidate.py','loaded_native_canonical_reload.py','native_place_serialization.py','staged_placement_reroute.py','native_route_ledger_import.py','persistent_rc_context.py')]]
(out/'protocol.json').write_text(json.dumps(dict(cases=cases,sources={str(p):sha(p) for p in sources},binaries={str(p):sha(p) for p in (binary,identity,shared/'build_tileplace_vpr/vpr/vpr')},scope='Live prediction, native target identity, serializer, same-target gate, canonical original FULL/STA/physical audits and ledger handoff included. One Python context per case; separate native process per update. Excludes initial native route/frontend/build. No durable/concurrent owner protocol or gain claim.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
def run(cmd,work,log,e):
    with log.open('w') as stream:return subprocess.run(cmd,cwd=work,env=e,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
results=[]
for case in cases:
    start=time.perf_counter();width=case['width'];bundle=Path(case['initial']);ctx=PersistentRCContext(case['original']);state=import_native_ledger(ctx,bundle/'design.route');rounds=[];error=None
    try:
        for step,target in enumerate(case['targets']):
            begin=time.perf_counter();work=out/f'gf2_d{width}_{step}';work.mkdir();probe=work/'identity_probe';probe.mkdir()
            result=stage_reroute_with_repair(state,target);candidate=result['repair'] or result['incremental'];assert candidate['failure'] is None
            (work/'prediction.json').write_text(json.dumps(candidate,indent=2)+'\n')
            for name in ('design.blif','design.net','design.place'):shutil.copyfile(bundle/name,work/name)
            shutil.copyfile(bundle/'design.route',work/'seed.route')
            for name in ('design.blif','design.net'):shutil.copyfile(bundle/name,probe/name)
            ep=json.loads(Path(target).read_text());place=Path(ep['inputs']['place']['path']);pos=placements(place,ep['inputs']['net']['sha256']);current=placements(bundle/'design.place',sha(bundle/'design.net'))
            moved=[n for n in current if current[n][:4]!=pos[n][:4]];assert len(moved)==2
            pair=' '.join(str(current[n][4]) for n in moved)
            lines=[f'Netlist_File: design.net Netlist_ID: SHA256:{sha(probe/"design.net")}',place.read_text().splitlines()[1],'']
            for block in ET.parse(probe/'design.net').getroot().findall('block'):
                name=block.get('name');x,y,z,layer,_=pos[name];lines.append(f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{current[name][4]}')
            (probe/'design.place').write_text('\n'.join(lines)+'\n');(probe/'design.place').write_text(canonical_place(probe/'design.place',probe/'design.net'))
            cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',ep['inputs']['graph']['path'],'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100']
            icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route')]='--analysis';icmd[icmd.index('--route_file')+1]='missing.route';table=probe/'identity.jsonl'
            assert run(icmd,probe,probe/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists()
            text,bindings=serialize(candidate,target,table,probe/'design.place');(work/'predicted.route').write_text(text)
            e={**env,'ROUTECAST_NATIVE_SEED':str(work/'seed.route'),'ROUTECAST_IMPORTED_CANDIDATE':str(work/'predicted.route'),'ROUTECAST_SAME_TARGET_GATE':'1','ROUTECAST_TIMING_RESTORE_PROBE':'1','ROUTECAST_MOVE_SEQUENCE':'A','ROUTECAST_MOVE_PAIRS':pair}
            assert run(cmd,work,work/'run.log',e)==0
            log=(work/'run.log').read_text();cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1])
            native=dict(width=width,decision='A',command=cmd,cpd_ns=cpd,files={str(p):sha(p) for p in work.rglob('*') if p.is_file()})
            reload=canonical_reload(native,work,work/'canonical')
            physical=audit(ep['inputs']['graph']['path'],work/'canonical/design.route');assert physical['overflow_units']==0 and len(physical['connections'])==len(candidate['records'])
            ctx.bind_endpoints(target);new_state=import_native_ledger(ctx,work/'canonical/design.route');state=new_state;bundle=work/'canonical'
            snapshot=work/'accepted_state.json';snapshot.write_text(json.dumps(dict(revision=step+1,records=[state.records[k] for k in sorted(state.records)],ledger=dict(state.ledger),endpoint_metadata=ctx.endpoint_metadata,scale=ctx.rc.scale),indent=2)+'\n')
            rounds.append(dict(step=step,wall_s=time.perf_counter()-begin,native=native,reload=reload,snapshot_sha256=sha(snapshot)))
            print(width,step,'accepted',cpd,flush=True)
    except Exception as ex:error=repr(ex)
    results.append(dict(width=width,case_wall_s=time.perf_counter()-start,rounds=rounds,error=error,complete=len(rounds)==2))
    assert all(sha(p)==h for p,h in case['inputs'].items())
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=results),indent=2)+'\n');print(width,'complete',error,flush=True)
