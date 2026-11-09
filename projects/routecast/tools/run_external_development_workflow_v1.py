"""Serial fixed-cohort execution with explicit dependency/failure and stage clocks.
Never retries a stage or replaces a failed case. Existing execution ledger is
refused; live work must be observed rather than restarted.
"""
import argparse,datetime,json,os,subprocess,sys,time
from pathlib import Path
from pre_route_endpoints import sha

def validate(path):
    path=Path(path).resolve();p=json.loads(path.read_text())
    if p['schema']!='ROUTECAST_EXTERNAL_EXECUTABLE_DEVELOPMENT_WORKFLOW_V1':raise ValueError('workflow schema')
    if not all(sha(q)==h for q,h in p['bindings'].items()):raise ValueError('workflow dependency changed')
    seen=set();outputs=set()
    for stage in p['stages']:
        if stage['id'] in seen or not set(stage['depends_on'])<=seen:raise ValueError('stage identity/order')
        seen.add(stage['id'])
        for output in stage['artifacts']:
            if output in outputs:raise ValueError('duplicate stage output')
            outputs.add(output)
        if stage['argv'][0]!=sys.executable or not Path(stage['argv'][1]).is_file():raise ValueError('executable')
    if len(p['target_cases'])!=9 or len(p['source_cases'])!=3:raise ValueError('cohort size')
    return p

def run(path):
    begin=time.perf_counter();p=validate(path);out=Path(p['execution_directory']);out.mkdir(exist_ok=False)
    ledger=out/'stages.json';results=[];status={}
    live=dict(pid=os.getpid(),started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),workflow=str(Path(path).resolve()))
    (out/'live_process.json').write_text(json.dumps(live)+'\n')
    for number,stage in enumerate(p['stages']):
        tick=time.perf_counter();row=dict(id=stage['id'],status='BLOCKED_DEPENDENCY',depends_on=stage['depends_on'])
        if stage.get('always_run') or all(status[x]=='PASS' for x in stage['depends_on']):
            for directory in stage['create_parents']:Path(directory).mkdir(parents=True,exist_ok=True)
            log=out/f'{number:03d}.log';start=dict(id=stage['id'],pid=os.getpid(),argv=stage['argv'],stage_started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            (out/'current_stage.json').write_text(json.dumps(start,indent=2)+'\n');print('STAGE_START',number,stage['id'],flush=True)
            try:
                with log.open('x') as stream:r=subprocess.run(stage['argv'],cwd=p['cwd'],stdout=stream,stderr=subprocess.STDOUT)
                row.update(exit_code=r.returncode,log=str(log),status='PASS' if r.returncode==0 else 'FAIL')
                if row['status']=='PASS':
                    row['artifacts']={q:sha(q) for q in stage['artifacts']}
                    for q,requirements in stage.get('required_json',{}).items():
                        data=json.loads(Path(q).read_text())
                        if any(data.get(k)!=v for k,v in requirements.items()):raise ValueError('terminal artifact gate: '+q)
            except Exception as e:row.update(status='FAIL',error=repr(e))
            print('STAGE_END',number,stage['id'],row['status'],flush=True)
        row['observed_stage_seconds']=time.perf_counter()-tick;status[stage['id']]=row['status'];results.append(row)
        tmp=ledger.with_suffix('.json.tmp');tmp.write_text(json.dumps(results,indent=2)+'\n');os.replace(tmp,ledger)
    result=dict(status='ALL_STAGES_TERMINAL',workflow_sha256=sha(path),stages=len(results),passed=sum(x['status']=='PASS' for x in results),failed=sum(x['status']=='FAIL' for x in results),blocked=sum(x['status']=='BLOCKED_DEPENDENCY' for x in results),continuous_execution_seconds_before_terminal_serialization=time.perf_counter()-begin,upstream_preparation_cost_complete=False,complete_workflow_gain_proven=False,strict_unseen_admitted=False,scope=p['timing_policy'])
    (out/'terminal.json').write_text(json.dumps(result,indent=2)+'\n');print('WORKFLOW_TERMINAL',json.dumps(result),flush=True)
    return result
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('workflow');a.add_argument('--preflight',action='store_true');args=a.parse_args()
    if args.preflight:print('WORKFLOW_PREFLIGHT_PASS',len(validate(args.workflow)['stages']))
    else:run(args.workflow)
