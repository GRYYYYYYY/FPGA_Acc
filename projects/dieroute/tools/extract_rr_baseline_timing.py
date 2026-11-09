"""Extract full native connection delays from the frozen VPR baseline route."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from audit_rr_experiments import audit

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('pair',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    pair=a.pair.resolve();out=a.output.resolve();audit(pair/'pair.json')
    manifest=json.loads((pair/'pair.json').read_text());case=Path(manifest['case'])
    connections=Path(manifest['reference'])/'connections.csv'
    out.mkdir(exist_ok=False)
    with connections.open() as stream:tasks=list(csv.DictReader(stream))
    input_file=out/'native_input.csv';output_file=out/'native_output.csv'
    with input_file.open('w') as stream:
        writer=csv.writer(stream)
        writer.writerow(['iteration','task_id','net_id','source','sink','routed','delay_ps','criticality_q'])
        for task in tasks:
            writer.writerow([0,task['id'],task['net_id'],task['source'],task['sink'],0,0,task['criticality_q']])
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(manifest['timing_environment']);env['PERSISTROUTE_VPR_ROUTE']=str(case/'circuit.route')
    adapter=pair/'source/persistroute/tools/vpr_timing_analyzer.py'
    command=['python3',str(adapter),'0',str(input_file),str(output_file)]
    files=[Path(__file__),pair/'pair.json',connections,adapter,input_file,Path(manifest['timing_vpr']['path']),
           *[case/name for name in ('architecture.xml','circuit.blif','circuit.net','circuit.place','circuit.route','rr_graph.xml','vpr.log')]]
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    inputs={str(path):sha(path) for path in files}
    state=dict(status='running',pid=os.getpid(),command=command,inputs=inputs,
               native_route=str(case/'circuit.route'),board_result=False,research_complete=False)
    def save():(out/'manifest.json').write_text(json.dumps(state,indent=2)+'\n')
    save()
    with (out/'run.log').open('w') as log:
        child=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT)
        state['child_pid']=child.pid;save();rc=child.wait()
    state.update(returncode=rc,inputs_unchanged=all(sha(Path(path))==h for path,h in inputs.items()),
                 status='failed' if rc else 'completed_requires_validation');save()
    assert rc==0 and state['inputs_unchanged']
    with output_file.open() as stream:rows=list(csv.DictReader(stream))
    assert {int(row['task_id']) for row in rows}=={int(task['id']) for task in tasks}
    assert len(rows)==len(tasks)
    cpds={int(row['critical_path_delay_ps']) for row in rows};assert len(cpds)==1
    expected=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',(case/'vpr.log').read_text())[-1])*1000
    assert abs(next(iter(cpds))-expected)<=1
    state.update(status='baseline_native_timing_extracted_and_cpd_checked',connections=len(rows),
                 native_cpd_ps=next(iter(cpds)),baseline_cpd_ps=expected,output_sha256=sha(output_file),
                 scope='Full native baseline delays, all input routed flags zero; CPD agrees with frozen VPR log. This is baseline timing evidence, not a new routing or causal path decomposition.')
    save();print(json.dumps({k:state[k] for k in ('status','connections','native_cpd_ps')}))
