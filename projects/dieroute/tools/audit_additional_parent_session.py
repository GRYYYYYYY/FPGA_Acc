"""Verify actual persistent session input/binary identities against frozen route configuration."""
import argparse,json
from pathlib import Path
import sys
sys.path.insert(1,'/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/dieroute/work/sb3_fixed_feedback_pair_20261015/native_tools')
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=Path);p.add_argument('online',type=Path);a=p.parse_args()
    pair,online=a.pair.resolve(),a.online.resolve()
    m=json.loads(pair.read_text());mode,=m['modes'];step=next(x for x in m['steps'] if x['label']==mode+'_0');env=step['routing_environment']
    run_path=online/'manifest.json';run=json.loads(run_path.read_text());assert run['status'] in ['online_router_completed_equivalence_audit_required','online_router_exit3_retained_orderly_session_stop_requires_capacity_classification']
    terminal_path=online/'router_process_terminal.json';launch_path=online/'router_process_launch.json';terminal=json.loads(terminal_path.read_text());launch=json.loads(launch_path.read_text())
    assert all(terminal[k]==launch[k] for k in launch) and terminal['returncode'] in (0,3)
    assert run['returncode']==terminal['returncode'] and run['raw_parent_legal_exit']==(terminal['returncode']==0)
    assert (run['status']=='online_router_completed_equivalence_audit_required')==(terminal['returncode']==0)
    assert launch['router_binary_sha256']==sha(Path(step['command'][0])) and launch['pair_sha256']==sha(pair)
    expected_router=list(step['command']);expected_router[3]=str(online/'route');assert terminal['command']==expected_router and terminal['cwd']==step['cwd']
    receipts_path=online/'timing_session/receipts.jsonl';receipts=[json.loads(line) for line in receipts_path.read_text().splitlines()]
    start=receipts[0];assert start['event']=='session_start'
    ready=[r for r in receipts if r['event']=='engine_ready'];assert len(ready)==1
    assert receipts[-1]['event']=='session_stop' and receipts[-1]['returncode']==0
    assert all(r['event']!='session_aborted_after_failure' for r in receipts)
    expected_inputs={str(Path(v).resolve()) for k,v in env.items() if k in ['PERSISTROUTE_VPR_ARCH','PERSISTROUTE_VPR_CIRCUIT','PERSISTROUTE_VPR_NET','PERSISTROUTE_VPR_PLACE','PERSISTROUTE_VPR_ROUTE','PERSISTROUTE_VPR_RR_GRAPH','PERSISTROUTE_VPR_CONSTRAINTS','PERSISTROUTE_VPR_SDC'] and v}
    binary=Path(start['command'][0]);expected_inputs.add(str(binary))
    assert set(start['input_sha256'])==expected_inputs,(set(start['input_sha256']),expected_inputs)
    assert all(sha(Path(name))==digest for name,digest in start['input_sha256'].items())
    assert sha(binary)==start['binary_sha256']==run['source_sha256'][str(binary)]
    adapter=pair.parent/'source/persistroute/tools/vpr_timing_analyzer.py';tasks=pair.parent/'input.tasks'
    assert sha(adapter)==start['adapter_sha256'] and sha(tasks)==start['tasks_sha256']
    command=start['command'];assert command[1:3]==[env['PERSISTROUTE_VPR_ARCH'],env['PERSISTROUTE_VPR_CIRCUIT']]
    assert command[command.index('--route_chan_width')+1]==env['PERSISTROUTE_VPR_CHAN_WIDTH']
    expected_flags={'PERSISTROUTE_VPR_DEVICE':'--device','PERSISTROUTE_VPR_RR_GRAPH':'--read_rr_graph','PERSISTROUTE_VPR_CONSTRAINTS':'--read_vpr_constraints'}
    for key,flag in expected_flags.items():
        if env.get(key):assert command[command.index(flag)+1]==env[key]
        else:assert flag not in command
    assert ready[0]['startup_ns']>0
    responses=[r for r in receipts if r['event']=='timing_response'];epochs=json.loads((online/'route.json').read_text())['iterations']
    assert len(responses)==epochs and [r['epoch'] for r in responses]==list(range(epochs)) and [r['sequence'] for r in responses]==list(range(epochs))
    for r in responses:
        assert sha(Path(r['input']))==r['input_sha256'] and sha(Path(r['output']))==r['output_sha256']
    report=dict(status='actual_parent_session_lineage_reviewed_raw_router_exit_retained',raw_router_returncode=terminal['returncode'],raw_parent_legal_exit=run['raw_parent_legal_exit'],epochs=epochs,input_files=len(expected_inputs),binary_sha256=start['binary_sha256'],source_sha256={str(p):sha(p) for p in [pair,run_path,receipts_path,adapter,tasks,terminal_path,launch_path,Path(__file__).resolve()]},scope='Raw router exit3 remains failure, not repaired/native quality pass. Checks archived process command and source identities against frozen pair,one READY and orderly STOP,all request hashes;not OS execution tracing,universal equivalence or performance measurement',board_result=False,research_complete=False)
    (online/'session_provenance_audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
