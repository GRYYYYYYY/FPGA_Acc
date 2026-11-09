"""Pinned upstream RTL/testbenches on locally extracted Icarus runtime."""
import sys,json,subprocess,re,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 src=R/'experiments/prospective_external_family_source_v2_2026-10-18';runtime=R/'experiments/prospective_external_family_sim_runtime_v1_2026-10-18';pkg=runtime/'iverilog_11.0-1.1_amd64.deb';assert sha(pkg)=='56b2b91e23f51c571b8cf43ef2df3a137a1bf4b6bcbff0fa3463b5b89403a852';tool=runtime/'root/usr/bin/iverilog';vvp=runtime/'root/usr/bin/vvp';lib=runtime/'root/usr/lib/x86_64-linux-gnu/ivl';rtl=sorted((src/'upstream/src/rtl').glob('*.v'));tb=sorted((src/'upstream/src/tb').glob('*.v'));assert len(rtl)==3 and len(tb)==2
 proof=src/'source_verification.json';admitted=json.loads(proof.read_text());out=R/'experiments/prospective_external_family_upstream_sim_v1_2026-10-18';out.mkdir(exist_ok=False);paths=[Path(__file__),pkg,tool,vvp,proof,*rtl,*tb,*[p for p in lib.iterdir() if p.is_file()]];bindings={str(p):sha(p) for p in paths};rows=[]
 for test in tb:
  d=out/test.stem;d.mkdir();image=d/'sim.vvp';command=[str(tool),'-B',str(lib),'-s',test.stem,'-o',str(image),*[str(p) for p in rtl],str(test)];tick=time.perf_counter()
  with (d/'compile.log').open('x') as log:code=subprocess.call(command,cwd=d,stdout=log,stderr=subprocess.STDOUT)
  assert code==0
  with (d/'simulation.log').open('x') as log:
   child=subprocess.Popen([str(vvp),'-M',str(lib),str(image)],cwd=d,stdout=log,stderr=subprocess.STDOUT);(d/'live_process.json').write_text(json.dumps(dict(pid=child.pid)));print('UPSTREAM SIM CHILD',test.stem,child.pid,flush=True);result=child.wait()
  text=(d/'simulation.log').read_text();success=result==0 and re.search(r'All (?:\d+ )?test cases completed successfully',text) is not None and 'ERROR' not in text and 'not complete successfully' not in text
  rows.append(dict(testbench=test.stem,compile_command=command,compile_exit_code=code,simulation_exit_code=result,upstream_summary_pass=success,component_seconds=time.perf_counter()-tick,files={str(p):sha(p) for p in d.iterdir() if p.is_file()}));print('UPSTREAM SIM RESULT',test.stem,success,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='both_upstream_source_testbenches_pass' if all(r['upstream_summary_pass'] for r in rows) else 'source_testbench_failure',bindings=bindings,rows=rows,scope='Original pinned RTL and two upstream testbenches, finite software simulation only. Not mapped/packed or placed design equivalence, independent new-vector coverage, STA, unseen-family qualification, route forecast or utility validation.'),f,indent=2)
if __name__=='__main__':main()
