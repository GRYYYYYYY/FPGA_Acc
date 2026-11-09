"""Account for archived per-epoch VPR process timing reports without claiming board speedup."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    pair=args.pair.resolve()
    assert not args.output.exists()
    manifest=json.loads(pair.read_text())
    assert manifest['status']=='completed'
    mode,=manifest['modes']
    data=manifest['modes'][mode]
    assert len(data['runs'])==5 and data['status']=='passed'
    assert manifest['configuration']['timing_updates'] and not manifest['configuration']['cleanup_passes']
    binary=Path(manifest['timing_vpr']['path'])
    assert sha(binary)==manifest['timing_vpr']['sha256']
    files=[pair,binary,Path(__file__).resolve()]
    results=[]
    for repeat,recorded in enumerate(data['runs']):
        raw=pair.parent/f'{mode}_{repeat}.json'
        assert json.loads(raw.read_text())==recorded
        step,=[s for s in manifest['steps'] if s['label']==f'{mode}_{repeat}']
        assert step['routing_environment']['DIEROUTE_TIMING_UPDATE_PERIOD']=='1'
        calls=[]
        for epoch in range(recorded['iterations']):
            log=pair.parent/f'{mode}_{repeat}.timing_iteration_{epoch}.output.csv.vpr.log'
            text=log.read_text()
            assert 'VPR succeeded' in text
            entire=re.findall(r'The entire flow of VPR took ([0-9.eE+-]+) seconds',text)
            analysis=re.findall(r'Flow timing analysis took ([0-9.eE+-]+) seconds \(([0-9.eE+-]+) STA, ([0-9.eE+-]+) slack\)',text)
            assert len(entire)==len(analysis)==1,(repeat,epoch)
            total=float(entire[0]);flow,sta,slack=map(float,analysis[0])
            assert 0<=sta<=flow<=total and 0<=slack<=flow
            calls.append(dict(epoch=epoch,tool_entire_flow_seconds=total,
                              tool_analysis_flow_seconds=flow,tool_sta_seconds=sta,tool_slack_seconds=slack))
            files.append(log)
        host=recorded['wall_ms']/1000
        total=sum(c['tool_entire_flow_seconds'] for c in calls)
        analysis=sum(c['tool_analysis_flow_seconds'] for c in calls)
        results.append(dict(repeat=repeat,host_wall_seconds=host,calls=calls,
                            tool_flow_seconds_sum=total,tool_analysis_seconds_sum=analysis,
                            tool_flow_outside_analysis_seconds_sum=total-analysis,
                            reported_flow_to_host_wall_ratio=total/host,
                            reported_analysis_to_host_wall_ratio=analysis/host,
                            host_wall_minus_reported_flow_seconds=host-total))
        files.append(raw)
    medians={key:statistics.median(r[key] for r in results) for key in (
        'host_wall_seconds','tool_flow_seconds_sum','tool_analysis_seconds_sum',
        'tool_flow_outside_analysis_seconds_sum','reported_flow_to_host_wall_ratio',
        'reported_analysis_to_host_wall_ratio','host_wall_minus_reported_flow_seconds')}
    report=dict(status='archived_serial_timing_process_reports_accounted',repeats=results,medians=medians,
                source_sha256={str(p):sha(p) for p in files},
                conclusion='Repeated process-level flow reports are large relative to the analysis-flow reports. '
                           'A persistent initialized analysis process is an appropriate controlled next experiment; '
                           'its output equivalence,startup cost and actual online integration must be validated.',
                scope='Observed shared-host CPU execution only. Rounded tool flow/analysis timers are summed '
                      'and compared to parent host wall;this is not an independently instrumented CPU partition. '
                      'Outside-analysis time includes initialization/loading/checking/other phases,not solely I/O. '
                      'No new optimization measured,controlled runtime benchmark,board speedup orresearchcompletion.',
                board_result=False,research_complete=False)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],medians=medians)))
