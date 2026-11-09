"""Preregistered ABBA, same complete audit runner and paid outer process boundary."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def main():
 out=R/'experiments/xtea_audit_context_abba_v1_2026-10-17';out.mkdir()
 model=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model';runner=R/'tools/run_independent_audit_context_mode_v2.py'
 proofs=[R/'experiments/xtea_shared_independent_audit_context_v1_2026-10-17/verification.json',R/'experiments/xtea_shared_independent_audit_negative_v1_2026-10-17/verification.json']
 for p in proofs:assert json.loads(p.read_text())['all_pass']
 files=[Path(__file__).resolve(),runner,*proofs,model/'receipt.json',model/'initial.json',model/'floors.json',model/'sketch.json'];bindings={str(p):sha(p) for p in files}
 order=['separate','shared','shared','separate']
 write(out/'protocol.json',dict(bindings=bindings,order=order,original_connections=2450,events=2896,only_change='Context acquisition and exact scale recomputation frequency; original full auditors unchanged, fork isolation in both modes.',primary_timer='External perf_counter from immediately before Popen through successful wait; includes Python import, independent original-graph parsing, scale scan, all original audit/hashing/binding/launch/output costs. Same runner for both modes. Cohort controller prelaunch proof validation and final comparison/report common excluded.',run_outputs='Fresh unique directory per arm, no parsed historical caches; normal OS caches not flushed or controlled.',decision='Report every arm and both order-reversed pair differences. Two repeats per mode are local descriptive evidence only, not statistical robustness, native workflow gain, heldout generalization or hardware proof.',no_retry_or_reordering=True,promoted=False))
 write(out/'process.json',dict(pid=os.getpid(),start_stat=Path('/proc/self/stat').read_text(),args=sys.argv))
 results=[]
 try:
  for i,mode in enumerate(order):
   assert all(sha(Path(p))==h for p,h in bindings.items())
   free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=10*2**30
   arm=out/f'arm{i}_{mode}';tick=time.perf_counter()
   with (out/f'arm{i}.log').open('x') as log:
    child=subprocess.Popen([sys.executable,str(runner),str(model),str(arm),mode],cwd=R,stdout=log,stderr=subprocess.STDOUT)
    write(out/f'arm{i}_process.json',dict(pid=child.pid,start_stat=Path('/proc',str(child.pid),'stat').read_text(),args=child.args))
    print('AUDIT CONTEXT ABBA START',i,mode,child.pid,flush=True)
    # Runner owns 600s per-child deadlines; never kill a batch owner while it has an active audit child.
    code=child.wait()
   elapsed=time.perf_counter()-tick;write(out/f'arm{i}_terminal.json',dict(exit_status=code,external_seconds=elapsed));assert code==0,'No retry'
   proof=json.loads((arm/'verification.json').read_text());assert proof['all_pass'] and proof['context_mode']==mode and proof['all_proofs_semantically_equal_closed_standalone_audits']
   assert proof['fresh_graph_context_loads']==(1 if mode=='shared' else 3)
   results.append(dict(index=i,mode=mode,external_seconds=elapsed,runner_internal_seconds=proof['full_batch_seconds'],proof_sha256=sha(arm/'verification.json')))
   print('AUDIT CONTEXT ABBA DONE',i,mode,elapsed,flush=True)
  for i,row in enumerate(results):
   proof=json.loads((out/f'arm{i}_{row["mode"]}'/'verification.json').read_text());assert all(sha(Path(p))==h for section in ['bindings','outputs'] for p,h in proof[section].items())
  assert all(sha(Path(p))==h for p,h in bindings.items())
  pairs=[dict(separate_index=a,shared_index=b,shared_minus_separate_seconds=results[b]['external_seconds']-results[a]['external_seconds'],shared_over_separate=results[b]['external_seconds']/results[a]['external_seconds']) for a,b in [(0,1),(3,2)]]
  write(out/'verification.json',dict(all_pass=True,all4_complete_three_audit_arms_and_semantic_parity=True,results=results,pairs=pairs,bindings=bindings,scope='Same-harness full local XTEA audit ABBA only; n2/mode, OS caches and shared-host variability retained. No native end-to-end gain.',promoted=False))
  write(out/'terminal.json',dict(exit_status=0,all_four_arms_complete=True));print('PASS complete ABBA',pairs,flush=True)
 except BaseException as error:
  write(out/'terminal.json',dict(exit_status=1,error_type=type(error).__name__,error=str(error),no_retry=True));raise
if __name__=='__main__':main()
