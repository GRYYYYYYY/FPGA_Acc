"""Full XML physical auditor must reject a privately inflated budget."""
import json,resource,subprocess,sys,time,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model';assert json.loads((src.parent/'pipeline_terminal.json').read_text())['all_stages_completed']
 out=R/'experiments/proxy_budget_full_auditor_negative_v1_2026-10-17';out.mkdir();model=out/'model';model.mkdir()
 original=sha(src/'initial.json')
 for p in src.iterdir():
  if p.name!='initial.json':(model/p.name).symlink_to(p)
 initial=json.loads((src/'initial.json').read_text());initial['records'][0]['budget_integer']+=1
 (model/'initial.json').write_text(json.dumps(initial)+'\n')
 auditor=R/'tools/verify_proxy_budget_demand_frame_v1.py';args=[sys.executable,str(auditor),str(model),'initial',str(out/'unexpected_success.json')];tick=time.perf_counter()
 with (out/'negative.log').open('x') as log:
  child=subprocess.Popen(args,stdout=log,stderr=subprocess.STDOUT,preexec_fn=lambda:resource.setrlimit(resource.RLIMIT_AS,(2**30,2**30)))
  (out/'process.json').write_text(json.dumps(dict(pid=child.pid,args=args,start_stat=Path('/proc',str(child.pid),'stat').read_text()))+'\n')
  try:code=child.wait(timeout=300)
  except subprocess.TimeoutExpired:
   child.terminate()
   try:child.wait(timeout=30)
   except subprocess.TimeoutExpired:child.kill();child.wait()
   raise
 log=(out/'negative.log').read_text();assert code==1 and 'rec[\'budget_integer\']==budget' in log and 'AssertionError' in log
 assert sha(src/'initial.json')==original and not (out/'unexpected_success.json').exists()
 result=dict(all_pass=True,expected_exit_status=code,seconds=time.perf_counter()-tick,private_budget_plus_one_rejected_at_formula_assertion=True,original_unchanged=True,bindings={str(p):sha(p) for p in [Path(__file__).resolve(),auditor,model/'initial.json',src/'initial.json',out/'negative.log']},promoted=False)
 (out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS full XML auditor refuses inflated budget')
if __name__=='__main__':main()
