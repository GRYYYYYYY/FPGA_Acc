"""Classify actual supplemental feedback by observed local-path delay changes."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pair=a.manifest.resolve();base=pair.parent;proof_path=a.audit.resolve()
    proof=json.loads(proof_path.read_text());assert proof['status']=='five_repeat_critical_feedback_pending_and_owner_replay_audited'
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in proof['source_sha256'].items())
    manifest=json.loads(pair.read_text());threshold=manifest['configuration']['criticality_feedback_threshold_q'];assert threshold>0
    files=[Path(__file__),pair,proof_path];outcomes={}
    def table(path):
        files.append(path)
        with path.open() as stream:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    for mode,result in proof['modes'].items():
        prefix=base/f'{mode}_0';inputs={};outputs={}
        for iteration in range(result['iterations']):
            inputs[iteration]={r['task_id']:r for r in table(Path(str(prefix)+f'.timing_iteration_{iteration}.input.csv'))}
            outputs[iteration]={r['task_id']:r for r in table(Path(str(prefix)+f'.timing_iteration_{iteration}.output.csv'))}
        events=[]
        for event in table(Path(str(prefix)+'.critical_feedback.csv')):
            if event['decision']!=1:continue
            iteration=event['iteration'];before=inputs[iteration];after=outputs[iteration]
            assert iteration>0
            crossings=[task for task,row in before.items() if row['net_id']==event['net_id'] and row['criticality_q']<threshold<=min(threshold,after[task]['criticality_q'])]
            assert crossings and min(crossings)==event['task_id']
            details=[]
            for task in crossings:
                previous=inputs[iteration-1][task];current=before[task]
                comparable=previous['routed']==current['routed']==1
                details.append(dict(task_id=task,comparable=comparable,previous_routed=previous['routed'],current_routed=current['routed'],
                    previous_delay_ps=previous['delay_ps'],current_delay_ps=current['delay_ps'],
                    delta_ps=current['delay_ps']-previous['delay_ps'] if comparable else None))
            increased=any(row['comparable'] and row['delta_ps']>0 for row in details)
            category='local_path_increased' if increased else 'not_all_paths_comparable' if not all(row['comparable'] for row in details) else 'no_local_path_increase'
            events.append(dict(**event,category=category,crossed_connections=details))
        assert len(events)==result['supplemental_events']
        outcomes[mode]=dict(supplemental_events=len(events),
            local_path_increased=sum(r['category']=='local_path_increased' for r in events),
            no_local_path_increase=sum(r['category']=='no_local_path_increase' for r in events),
            not_comparable=sum(r['category']=='not_all_paths_comparable' for r in events),events=events)
    report=dict(status='observed_supplemental_feedback_delay_changes_profiled',modes=outcomes,
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                scope='Classifies only the executed candidate trajectory using local path-delay inputs and actual cap crossings. Includes all crossing connections per net, not just its logged representative. No counterfactual outcome, causal global-CPD attribution, native timing bound or proposed-filter benefit is established.',
                research_complete=False,board_result=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({mode:{k:v for k,v in result.items() if k!='events'} for mode,result in outcomes.items()}))
