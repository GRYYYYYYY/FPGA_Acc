"""Frozen isolated pack-only readiness; no placement, route or family admission."""
import hashlib,json,os,resource,shutil,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 auditpath=R/'experiments/wbuart_equivalence_keepdc_coverage_v1_2026-10-20/verification.json';audit=json.loads(auditpath.read_text());assert audit['status']=='ALL599_GATE_STATES_AND40_OUTPUTS_COVERED_NO_CONSTANT_FOLDED_STATE'
 for p,h in audit['bindings'].items():assert sha(p)==h
 source=R/'experiments/wbuart_boolean_cut_keepdc_v1_2026-10-20/design.blif';vpr=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_vpr/vpr/vpr';arch=R/'experiments/async_reset_arch_candidate_v2_2026-10-08/architecture.xml';assert vpr.is_file()
 out=R/'experiments/wbuart_pack_v1_2026-10-20';out.mkdir(exist_ok=False);shutil.copyfile(source,out/'design.blif');bindings={str(p):sha(p) for p in [auditpath,source,vpr,arch,Path(__file__),out/'design.blif']};command=[str(vpr),str(arch),'design.blif','--pack','--net_file','design.net','--route_chan_width','128','--num_workers','1','--seed','1']
 protocol=dict(bindings=bindings,command=command,AS_limit_bytes=8*2**30,timeout_seconds=None,scope='Source preparation only: full unchanged mapped circuit, one fixed pack-only invocation. No target layout/route label, performance-based source selection or strict-family assignment. All original source/HDL/unknown-history gaps remain explicit. Header-only place output allowed only with zero data rows.')
 with (out/'protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
 env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 start=time.perf_counter()
 with (out/'pack.log').open('x') as log:
  child=subprocess.Popen(command,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  with (out/'live_process.json').open('x') as f:json.dump(dict(pid=child.pid,command=command,source='wrapper-owned child, no competing recovery or queue'),f,indent=2)
  print('PACK CHILD PID',child.pid,flush=True);code=child.wait()
 elapsed=time.perf_counter()-start
 rows=[]
 for path in out.glob('*.place'):
  rows.extend(line for line in path.read_text().splitlines() if line.strip() and not line.startswith(('#','Netlist_File:','Array size:')))
 assert not rows and not list(out.glob('*.route'))
 for p,h in bindings.items():assert sha(p)==h
 success=code==0 and (out/'design.net').exists() and 'VPR succeeded' in (out/'pack.log').read_text();files={str(p):sha(p) for p in out.iterdir() if p.is_file()}
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='pack_success_pending_full_FF_pin_audit' if success else 'pack_failed',bindings=bindings,files=files,exit_code=code,component_seconds=elapsed,placement_data_rows=0,new_native_route_labels=False,strict_unseen_admitted=False,scope=protocol['scope']),f,indent=2)
 print('PACK PREFLIGHT TERMINAL',code,success,flush=True)
 if not success:raise SystemExit(code or 1)
if __name__=='__main__':main()
