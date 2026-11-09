"""Serial independent-execution repeat with full stage timers and frozen algorithms."""
import hashlib,json,os,subprocess,time,traceback
from pathlib import Path
import run_native_joint_budget_repeat_stage as sweep
import run_native_refreshed_critical_policy_v1 as refresh

R=Path(__file__).resolve().parents[1]
D=R/'work/native_instrumented_compound_repeat_20261016'
def atomic(path,obj):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(obj,indent=2)+'\n');temp.replace(path)

def main():
    protocol=json.loads((D/'protocol.json').read_text())
    for file,h in protocol['source_sha256'].items():assert hashlib.sha256(Path(file).read_bytes()).hexdigest()==h,file
    begin=time.monotonic_ns();state=dict(status='running',pid=os.getpid(),cases=[],stages=[],research_complete=False,adopted=False)
    atomic(D/'manifest.json',state)
    try:
        for case in protocol['cases']:
            case_begin=time.monotonic_ns();label=case['label']
            for step in case['repeat_parent_commands']:
                start=time.monotonic_ns();record=dict(case=label,label=step['label'],command=step['command'],status='running')
                state['stages'].append(record);atomic(D/'manifest.json',state)
                with (D/(step['label']+'.log')).open('x') as log:
                    process=subprocess.Popen(step['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT)
                    record['pid']=process.pid;atomic(D/'manifest.json',state);rc=process.wait()
                record.update(status='terminal',returncode=rc,wall_ns=time.monotonic_ns()-start);atomic(D/'manifest.json',state)
                assert rc==0,(step['label'],rc)
            results=[]
            for name,module in [('sweep',sweep),('refresh',refresh)]:
                module.P=D/name;module.P.mkdir(exist_ok=True)
                if name=='refresh':case['policy_parent_tree']=results[0]['current_tree']
                start=time.monotonic_ns();record=dict(case=label,label=name,status='running');state['stages'].append(record);atomic(D/'manifest.json',state)
                result=module.run_case(case,protocol);results.append(result)
                record.update(status='terminal',wall_ns=time.monotonic_ns()-start,quality=result['current_quality']);atomic(D/'manifest.json',state)
            state['cases'].append(dict(case=label,wall_ns=time.monotonic_ns()-case_begin,final_tree=results[-1]['current_tree'],quality=results[-1]['current_quality'],crossings=results[-1]['final_crossings']))
            atomic(D/'manifest.json',state)
        state.update(status='three_case_compound_repeat_terminal_requires_independent_review',wall_ns=time.monotonic_ns()-begin);atomic(D/'manifest.json',state)
    except BaseException as error:
        state.update(status='failed_preserve_evidence',wall_ns=time.monotonic_ns()-begin,error=repr(error),traceback=traceback.format_exc());atomic(D/'manifest.json',state);raise

if __name__=='__main__':main()
