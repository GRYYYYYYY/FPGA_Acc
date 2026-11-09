"""Raw original-native FULL/STA evaluation of independently audited repaired state."""
import json,os,re,shutil,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from serialize_live_native_candidate import serialize
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux32_shortest_first_tree_2026-10-07';cp=base/'candidate.json';rp=base/'receipt.json';vp=base/'verification.json';r=json.loads(rp.read_text());v=json.loads(vp.read_text());assert r['candidate_sha256']==sha(cp) and v['receipt_sha256']==sha(rp);c=json.loads(cp.read_text())
ep=ROOT/'experiments/mux_budget_move_cohort_2026-10-06/w32_m2/target_endpoints.json';endpoints=json.loads(ep.read_text());assert all(sha(x['path'])==x['sha256'] for x in endpoints['inputs'].values())
shared=ROOT.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';binary=shared/'build_tileplace_vpr/vpr/vpr';arch=shared/'vtr_flow/arch/timing/k6_frac_N10_40nm.xml';identity=ROOT/'build/native_net_identity_capture_2026-10-06/routecast_net_identity_vpr';blif=ROOT/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128/design.blif'
out=ROOT/'experiments/mux32_shortest_first_native_2026-10-07';out.mkdir(exist_ok=False)
protocol=dict(sources=closure([Path(__file__)]),inputs={str(p):sha(p) for p in (cp,rp,vp,ep,binary,arch,identity,blif)},timeout_s=180,scope='Raw native FULL/STA characterization of repaired development candidate. Packing synchronization may fix traces; canonical zero-fixup/path preservation still required. Not final accepted state or complete netgain.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.perf_counter();env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};result={}
def run(cmd,log,environment):
 with (out/log).open('w') as stream:return subprocess.run(cmd,cwd=out,env=environment,stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
try:
 for src,name in [(blif,'design.blif'),(Path(endpoints['inputs']['net']['path']),'design.net'),(Path(endpoints['inputs']['place']['path']),'design.place')]:shutil.copyfile(src,out/name)
 cmd=[str(binary),str(arch),'design.blif','--analysis','--net_file','design.net','--place_file','design.place','--route_file','design.route','--read_rr_graph',endpoints['inputs']['graph']['path'],'--route_chan_width','128','--num_workers','1','--check_route','full']
 icmd=cmd.copy();icmd[0]=str(identity);icmd[icmd.index('--route_file')+1]='missing.route';table=out/'identity.jsonl';code=run(icmd,'identity.log',{**env,'ROUTECAST_NET_IDENTITY_FILE':str(table)});assert code==1 and table.exists()
 text,bindings=serialize(c,ep,table,out/'design.place');(out/'design.route').write_text(text);(out/'bindings.json').write_text(json.dumps(bindings,indent=2)+'\n');serialized=sha(out/'design.route');code=run(cmd,'import.log',env);log=(out/'import.log').read_text();assert code==0 and 'Completed routing consistency check successfully.' in log and 'VPR succeeded' in log
 result=dict(status='RAW_NATIVE_FULL_STA_SUCCESS',native_exit_code=code,cpd_ns=re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1],wirelength=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]),serialized_input_sha256=serialized,serialized_file_unchanged=serialized==sha(out/'design.route'),packing_mismatches=re.findall(r'Found (\d+) mismatches',log),packing_fixups=re.findall(r'Fixed (\d+) routing traces',log),command=cmd)
except Exception as ex:result=dict(status='IMPORT_FAILED',error=repr(ex))
assert all(sha(p)==h for p,h in {**protocol['sources'],**protocol['inputs']}.items())
result.update(protocol_sha256=sha(out/'protocol.json'),seconds=time.perf_counter()-start,files={str(p):sha(p) for p in out.iterdir() if p.is_file()},scope=protocol['scope']);(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'],result.get('error'),result.get('cpd_ns'),result.get('wirelength'))
