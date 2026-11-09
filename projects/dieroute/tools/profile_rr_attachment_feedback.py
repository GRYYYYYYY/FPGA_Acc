"""Join verified actual attachment choices and final routing criticalities."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('variant',type=Path);p.add_argument('index',type=int,choices=(0,1))
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    base=a.variant.resolve();files=[Path(__file__)]
    def read(path):files.append(path);return json.loads(path.read_text())
    def table(path):
        files.append(path)
        with path.open() as stream:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    protocol=read(base/'protocol.json')
    replay=read(base/f'attachment_audit_{a.index}.json')
    compatible=read(base/f'compatibility_{a.index}.json')
    routing=read(base/f'routing_audit_{a.index}.json')['experiments'][0]
    assert replay['status']=='five_repeat_attachment_replay_audited'
    assert compatible['status']=='five_repeat_attachment_trace_compatibility_audited'
    for proof in (replay,compatible):
        assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in proof['source_sha256'].items())
    pair=Path(protocol['commands'][a.index][4]);manifest=read(pair/'pair.json')
    result=routing['modes']['downstream_bounded'];config=manifest['configuration']
    assert result['status']=='passed' and result['repeats_verified']==5
    prefix=pair/'downstream_bounded_0'
    accepted=table(Path(str(prefix)+'.attachments.csv'));latest={}
    for row in accepted:latest[row['task_id']]=row
    final_iteration=result['counters']['iterations']-1;cap=config['criticality_cap_q']
    final={r['task_id']:r for r in table(Path(str(prefix)+f'.timing_iteration_{final_iteration}.output.csv'))}
    assert latest.keys()==final.keys()
    changed=[];all_latest=[]
    for task,row in latest.items():
        final_criticality=min(cap,final[task]['criticality_q'])
        detail=dict(**row,final_routing_criticality_q=final_criticality,
                    local_total_delay_q=row['prefix_delay_q']+row['branch_delay_q'])
        all_latest.append(detail)
        if row['criticality_q']<cap and final_criticality==cap:changed.append(detail)
    changed.sort(key=lambda r:(-r['local_total_delay_q'],r['task_id']))
    all_latest.sort(key=lambda r:(-r['prefix_delay_q'],r['task_id']))
    report=dict(status='actual_attachment_and_final_feedback_joined',
                weight=config['route_tree_timing_weight_q'],accepted_rows=len(accepted),
                tasks=len(latest),final_iteration=final_iteration,
                final_capped=sum(min(cap,r['criticality_q'])==cap for r in final.values()),
                final_capped_with_last_acceptance_below_cap=changed,
                largest_last_accepted_prefixes=all_latest[:20],native_qor=result['native_qor'],
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                scope='Actual last accepted proposals after five-repeat CSR/tree/seed replay and original-output compatibility. Final criticality is the routed local-delay STA feedback, not a counterfactual or causal CPD explanation. No subsequent accepted proposal does not imply that extra rerouting would improve QoR.',
                board_result=False,research_complete=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],weight=report['weight'],
                         final_capped=report['final_capped'],not_accepted_at_final_cap=len(changed),top=changed[:3])))
