"""Run all six prospectively fixed diagnostic cells once, retain every outcome."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def run(manifest):
    begin=time.perf_counter();manifest=Path(manifest).resolve();m=json.loads(manifest.read_text())
    if len(m['cases'])!=6 or not all(sha(p)==h for p,h in m['bindings'].items()):raise ValueError('fixed diagnostic bindings')
    out=manifest.parent/'execution';out.mkdir(exist_ok=False);(out/'live_process.json').write_text(json.dumps(dict(pid=os.getpid(),manifest=str(manifest)))+'\n');rows=[]
    for index,job in enumerate(m['cases']):
        command=[sys.executable,str(R/'tools/run_external_native_route_case_v1.py'),str(manifest),job['case']];tick=time.perf_counter();print('DIAGNOSTIC_START',job['case'],flush=True)
        (out/'current_case.json').write_text(json.dumps(dict(case=job['case'],argv=command))+'\n')
        with (out/f'{index:02d}.log').open('x') as log:r=subprocess.run(command,cwd=R,stdout=log,stderr=subprocess.STDOUT)
        proof=Path(job['output'])/'verification.json';result=json.loads(proof.read_text()) if proof.exists() else {}
        rows.append(dict(case=job['case'],width=job['width'],termination_policy=job['termination_policy'],exit_code=r.returncode,native_exit_code=result.get('exit_status'),status=result.get('status','EXECUTOR_FAILED'),verification=str(proof),seconds=time.perf_counter()-tick));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print('DIAGNOSTIC_END',job['case'],rows[-1]['status'],flush=True)
    (out/'terminal.json').write_text(json.dumps(dict(status='ALL6_FIXED_TERMINATION_DIAGNOSTICS_TERMINAL',rows=rows,continuous_seconds_before_terminal_serialization=time.perf_counter()-begin,primary_cohort_replaced=False,forecast_or_utility_claim=False),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest');a=p.parse_args();run(a.manifest)
