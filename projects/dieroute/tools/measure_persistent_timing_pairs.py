"""Five alternating paired CPU timings, identical router/native binary and artifact checks."""
import argparse
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import time
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pair',type=Path);p.add_argument('build',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();pair,build,output=[x.resolve() for x in (a.pair,a.build,a.output)]
    output.mkdir(exist_ok=False)
    tools=Path(__file__).resolve().parent
    source=json.loads(pair.read_text());mode,=source['modes']
    step=next(s for s in source['steps'] if s['label']==mode+'_0')
    binary=Path(json.loads((build/'build_dependency_audit.json').read_text())['binary'])
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(step['routing_environment']);env['PERSISTROUTE_VPR_BIN']=str(binary)
    records=[]
    report=dict(status='running',pid=os.getpid(),pairs=5,order='fresh/persistent on even pairs,persistent/fresh on odd pairs',records=records,source_sha256={str(f):sha(f) for f in [pair,binary,*tools.glob('*.py')]},scope='Shared-host CPU router plus STA flow;outer subprocess wall includes persistent startup/shutdown. Five pairs,all semantic artifacts checked;no physical-card claim.',board_result=False,research_complete=False)
    def save(): (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    save()
    try:
        for index in range(5):
            for transport in (['fresh','persistent'] if index%2==0 else ['persistent','fresh']):
                directory=output/f'pair_{index}_{transport}'
                if transport=='fresh':
                    directory.mkdir()
                    command=list(step['command']);command[3]=str(directory/'route')
                    cwd=step['cwd']
                else:
                    command=[sys.executable,str(tools/'run_persistent_timing_online.py'),str(pair),str(build),str(directory)]
                    cwd=str(pair.parent)
                record=dict(pair=index,transport=transport,command=command,load_before=os.getloadavg(),status='running')
                records.append(record);save()
                begin=time.monotonic_ns()
                with (output/f'pair_{index}_{transport}.log').open('w') as log:
                    child=subprocess.Popen(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
                    record['pid']=child.pid;save()
                    code=child.wait()
                elapsed=time.monotonic_ns()-begin
                record.update(returncode=code,outer_elapsed_ns=elapsed,load_after=os.getloadavg())
                assert code==0,(index,transport,code)
                if transport=='fresh':
                    (directory/'manifest.json').write_text(json.dumps(dict(status='online_router_completed_equivalence_audit_required',requests=source['modes'][mode]['runs'][0]['iterations'],transport='fresh',native_binary_sha256=sha(binary)),indent=2)+'\n')
                with (output/f'pair_{index}_{transport}_audit.log').open('w') as log:
                    subprocess.run([sys.executable,str(tools/'audit_persistent_timing_online.py'),str(pair),str(directory)],stdout=log,stderr=subprocess.STDOUT,check=True)
                record.update(status='completed_and_artifacts_audited',audit_sha256=sha(directory/'equivalence_audit.json'));save()
        ratios=[]
        for index in range(5):
            values={r['transport']:r['outer_elapsed_ns'] for r in records if r['pair']==index}
            ratios.append(values['fresh']/values['persistent'])
        report.update(status='five_alternating_cpu_pairs_complete_all_artifacts_audited',paired_ratios=ratios,median_paired_ratio=statistics.median(ratios),median_fresh_seconds=statistics.median(r['outer_elapsed_ns']/1e9 for r in records if r['transport']=='fresh'),median_persistent_seconds=statistics.median(r['outer_elapsed_ns']/1e9 for r in records if r['transport']=='persistent'))
    except BaseException as error:
        report.update(status='failed',error=repr(error));raise
    finally: save()
