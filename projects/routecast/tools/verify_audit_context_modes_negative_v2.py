"""Both actual same-harness modes must refuse an inflated private initial budget."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 abba=R/'experiments/xtea_audit_context_abba_v1_2026-10-17';assert json.loads((abba/'verification.json').read_text())['all_pass']
 out=R/'experiments/xtea_audit_context_modes_negative_v2_2026-10-17';out.mkdir();src=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model';runner=R/'tools/run_independent_audit_context_mode_v2.py';original=sha(src/'initial.json');results={}
 bindings={str(p):sha(p) for p in [Path(__file__).resolve(),runner,abba/'verification.json',src/'initial.json']}
 for mode in ['separate','shared']:
  free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=10*2**30
  root=out/mode;root.mkdir();model=root/'model';model.mkdir()
  for p in src.iterdir():
   if p.name!='initial.json':(model/p.name).symlink_to(p)
  initial=json.loads((src/'initial.json').read_text());initial['records'][0]['budget_integer']+=1;write(model/'initial.json',initial)
  tick=time.perf_counter()
  with (root/'runner.log').open('x') as log:
   child=subprocess.Popen([sys.executable,str(runner),str(model),str(root/'batch'),mode],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   write(root/'process.json',dict(pid=child.pid,start_stat=Path('/proc',str(child.pid),'stat').read_text(),args=child.args));print('MODE NEGATIVE START',mode,child.pid,flush=True)
   code=child.wait()
  stage=json.loads((root/'batch/initial_terminal.json').read_text());terminal=json.loads((root/'batch/terminal.json').read_text());log=(root/'batch/initial.log').read_text()
  assert code==stage['exit_status']==terminal['exit_status']==1 and not stage['timed_out']
  assert 'AssertionError' in log and "rec['budget_integer']==budget" in log
  assert not (root/'batch/verification.json').exists() and not (root/'batch/sketch_process.json').exists() and sha(src/'initial.json')==original
  results[mode]=dict(inflated_budget_refused_by_original_full_XML_auditor=True,subsequent_stages_not_started=True,unexpected_success_proof_absent=True,exit_status=code,seconds=time.perf_counter()-tick)
  for p in [model/'initial.json',root/'batch/initial.log',root/'batch/terminal.json']:bindings[str(p)]=sha(p)
 assert all(sha(Path(p))==h for p,h in bindings.items())
 write(out/'verification.json',dict(all_pass=True,both_actual_modes_corrupt_budget_refused=True,original_inputs_unchanged=True,results=results,bindings=bindings,promoted=False));print('PASS both modes refuse corrupt budget',flush=True)
if __name__=='__main__':main()
