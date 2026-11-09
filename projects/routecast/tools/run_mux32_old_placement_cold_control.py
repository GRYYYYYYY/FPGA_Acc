"""Independent prepared-input cold route plus canonical physical/endpoint proof."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from freeze_priority_family import closure
from loaded_native_canonical_reload import canonical_reload
from stream_native_route_audit_cached import audit
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_old_placement_cold_control_2026-10-07';out.mkdir(exist_ok=False)
source=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128';ep=ROOT/'experiments/mux_live_placement_updates_2026-10-06/w32/original_endpoints.json';endpoints=json.loads(ep.read_text());shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';binary=shared/'build_tileplace_vpr/vpr/vpr';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';graph=Path(endpoints['inputs']['graph']['path']);inputs=[ep,source/'design.blif',Path(endpoints['inputs']['net']['path']),Path(endpoints['inputs']['place']['path']),graph,binary,arch]
protocol=dict(sources=closure([Path(__file__)]),inputs={str(p):sha(p) for p in inputs},seed=1,timeout_s=180,scope='Old-placement cold control. Copy mapped blif/packed net/unchanged original placement, fresh original route FULL/STA, canonical zero-fixup replay and independent physical/target endpoint proof all included. No candidate/native proposed-state oracle input. Graph, initial predictor and original-input conversion preparation excluded; route parameters match target cohort except explicitly spelling default seed1; single serial observation.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for sourcefile,name in [(source/'design.blif','design.blif'),(Path(endpoints['inputs']['net']['path']),'design.net'),(Path(endpoints['inputs']['place']['path']),'design.place')]:shutil.copyfile(sourcefile,out/name)
cmd=[str(binary),str(arch),'design.blif','--route','--net_file','design.net','--place_file','design.place','--route_file','output.route','--read_rr_graph',str(graph),'--route_chan_width','128','--num_workers','1','--check_route','full','--max_router_iterations','100','--seed','1']
with (out/'route.log').open('w') as stream:code=subprocess.run(cmd,cwd=out,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
log=(out/'route.log').read_text();assert code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log
cpd=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1];wire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);p=dict(width=32,decision='R',command=cmd,cpd_ns=float(cpd),files={str(f):sha(f) for f in out.iterdir() if f.is_file()})
canonical=canonical_reload(p,out,out/'canonical');assert canonical['mismatches']==canonical['fixups']==0;route=out/'canonical/design.route';physical=audit(graph,route);assert physical['overflow_units']==0 and len(physical['connections'])==1929
paths=physical_paths(route);before=physical_paths(out/'output.route');assert {name:Counter(rows) for name,rows in paths.items() if rows}=={name:Counter(rows) for name,rows in before.items() if rows}
observed=Counter((name,row[0][0],row[-1][0]) for name,rows in paths.items() for row in rows);expected=Counter((endpoints['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in endpoints['connections']);assert observed==expected
clog=(out/'canonical/reload.log').read_text();assert int(re.findall(r'Total wirelength:\s*(\d+)',clog)[-1])==wire
assert all(sha(f)==h for f,h in {**protocol['sources'],**protocol['inputs']}.items())
r=dict(protocol_sha256=sha(out/'protocol.json'),external_wall_seconds=time.perf_counter()-start,native_exit_code=code,command=cmd,cpd_ns=cpd,wirelength=wire,canonical=canonical,physical_audit=physical,target_endpoints_match=True,files={str(f):sha(f) for f in out.iterdir() if f.is_file()},scope=protocol['scope']);(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(r['external_wall_seconds'],cpd,wire)
