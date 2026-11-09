"""All mux outcomes retained; submit only complete audited candidates."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from pre_route_endpoints import placements,sha
from serialize_live_native_candidate import serialize
from loaded_native_canonical_reload import canonical_reload

ROOT=Path(__file__).resolve().parents[1]
parent=ROOT/'experiments/mux_owner_wire_50ps_development_2026-10-07'
pr=json.loads((parent/'receipt.json').read_text());pr['rows']=[r for r in pr['rows'] if (r['width'],r['index'])==(8,3)];assert len(pr['rows'])==1;pp=json.loads((parent/'protocol.json').read_text())
pp['cases']=[c for c in pp['cases'] if (c['width'],c['index'])==(8,3)]
for spec in pp['cases']:
    ep=json.loads(Path(spec['target']).read_text());spec['source']=str(Path(ep['inputs']['net']['path']).parent);spec['swapped']=ep['inputs']['place']['path']
assert json.loads((parent/'w8_m3/native_input_verification.json').read_text())['result_sha256']==pr['rows'][0]['result_sha256']
out=ROOT/'experiments/mux_native_joint_50ps_w8m3_quality_gate_2026-10-07';out.mkdir();(out/'parent_receipt_snapshot.json').write_text(json.dumps(pr,indent=2)+'\n')
binary=ROOT/'build/native_joint_qor_gate_2026-10-07/gate_vpr'
identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr'
arch=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vtr_flow/arch/timing/k6_frac_N10_40nm.xml'
sources=[Path(__file__),ROOT/'tools/serialize_live_native_candidate.py',ROOT/'tools/loaded_native_canonical_reload.py']
(out/'protocol.json').write_text(json.dumps(dict(parent_receipt_sha256=sha(out/'parent_receipt_snapshot.json'),native_input_verification_sha256=sha(parent/'w8_m3/native_input_verification.json'),cases=pp['cases'],sources={str(p):sha(p) for p in sources},binaries={str(p):sha(p) for p in (binary,identity,arch)},scope='Focused w8m3 ONLY complete audited fixed-cap candidate, actual-model pass independently checked. Gate also computes same-target coldreference; selectedoutput is not necessarily candidate. One-step loaded same-target native joint CPD/wire quality gate and original canonical FULL/STA; not live whole-cost benchmark.'),indent=2)+'\n')
env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
def run(cmd,work,log,e):
    with log.open('w') as stream:return subprocess.run(cmd,cwd=work,env=e,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
rows=[]
for spec,prediction_row in zip(pp['cases'],pr['rows']):
    width=spec['width'];index=spec['index'];work=out/f'w{width}_m{index}';work.mkdir()
    if prediction_row['status']=='ALLOCATION_NOT_SUBMITTED':
        rows.append(dict(width=width,index=index,status='ALLOCATION_NOT_SUBMITTED',failure=prediction_row['failure']));continue
    candidate=json.loads((parent/f'w{width}_m{index}/result.json').read_text())['result']['candidate']
    assert sha(parent/f'w{width}_m{index}/result.json')==prediction_row['result_sha256']
    if candidate['failure'] is not None:
        rows.append(dict(width=width,index=index,status='INCOMPLETE_NOT_SUBMITTED',failure=candidate['failure']));continue
    source=Path(spec['source']);probe=work/'identity_probe';probe.mkdir();row=dict(width=width,index=index,status='FAILED');error=None
    try:
        for name in ('design.blif','design.net','design.place'):shutil.copyfile(source/name,work/name)
        shutil.copyfile(source/'design.route',work/'seed.route')
        for name in ('design.blif','design.net'):shutil.copyfile(source/name,probe/name)
        shutil.copyfile(spec['swapped'],probe/'design.place')
        positions=placements(source/'design.place',sha(source/'design.net'));pair=' '.join(str(positions[n][4]) for n in spec['pair'])
        graph=source/'rr_graph.xml';cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100']
        icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route')]='--analysis';icmd[icmd.index('--route_file')+1]='missing.route';table=probe/'identity.jsonl'
        assert run(icmd,probe,probe/'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)})==1 and table.exists()
        text,bindings=serialize(candidate,Path(spec['target']),table,probe/'design.place');(work/'predicted.route').write_text(text);(work/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n')
        e={**env,'ROUTECAST_NATIVE_SEED':str(work/'seed.route'),'ROUTECAST_IMPORTED_CANDIDATE':str(work/'predicted.route'),'ROUTECAST_SAME_TARGET_GATE':'1','ROUTECAST_TIMING_RESTORE_PROBE':'1','ROUTECAST_MOVE_SEQUENCE':'A','ROUTECAST_MOVE_PAIRS':pair}
        code=run(cmd,work,work/'run.log',e);row['native_exit_code']=code;assert code==0
        log=(work/'run.log').read_text();cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1])
        native=dict(width=width,decision='A',command=cmd,cpd_ns=cpd,files={str(p):sha(p) for p in work.rglob('*') if p.is_file()})
        reload=canonical_reload(native,work,work/'canonical')
        row.update(status='RELOADED',native=native,reload=reload)
    except Exception as ex:error=repr(ex)
    row['error']=error;rows.append(row)
    assert all(sha(p)==h for p,h in spec['inputs'].items())
    print(width,row['status'],error,flush=True)
    (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
