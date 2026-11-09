"""Inflated private budget must fail through the same fresh shared-context audit runner."""
import json,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 positive=R/'experiments/xtea_shared_independent_audit_context_v1_2026-10-17';assert json.loads((positive/'verification.json').read_text())['all_pass']
 src=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model';original=sha(src/'initial.json')
 out=R/'experiments/xtea_shared_independent_audit_negative_v1_2026-10-17';out.mkdir();model=out/'model';model.mkdir()
 for p in src.iterdir():
  if p.name!='initial.json':(model/p.name).symlink_to(p)
 initial=json.loads((src/'initial.json').read_text());initial['records'][0]['budget_integer']+=1;(model/'initial.json').write_text(json.dumps(initial)+'\n')
 runner=R/'tools/run_shared_independent_audits_v1.py';tick=time.perf_counter()
 with (out/'runner.log').open('x') as log:
  child=subprocess.Popen([sys.executable,str(runner),str(model),str(out/'batch')],cwd=R,stdout=log,stderr=subprocess.STDOUT)
  (out/'process.json').write_text(json.dumps(dict(pid=child.pid,start_stat=Path('/proc',str(child.pid),'stat').read_text(),args=child.args))+'\n')
  # Runner owns child timeout and limits. Do not terminate the owner while its child is active.
  code=child.wait()
 assert code==1
 terminal=json.loads((out/'batch/terminal.json').read_text());stage=json.loads((out/'batch/initial_terminal.json').read_text());assert terminal['exit_status']==stage['exit_status']==1 and not stage['timed_out']
 log=(out/'batch/initial.log').read_text();assert 'AssertionError' in log and "rec['budget_integer']==budget" in log
 assert not (out/'batch/verification.json').exists() and not (out/'batch/sketch_process.json').exists() and sha(src/'initial.json')==original
 result=dict(all_pass=True,actual_shared_context_full_XML_auditor_refuses_budget_plus_one=True,no_following_audits_or_success_proof=True,original_model_unchanged=True,seconds=time.perf_counter()-tick,bindings={str(p):sha(p) for p in [Path(__file__).resolve(),runner,positive/'verification.json',src/'initial.json',model/'initial.json',out/'batch/initial.log',out/'batch/terminal.json']},promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS shared-context original auditor rejects corrupt budget; no retry or next stage')
if __name__=='__main__':main()
