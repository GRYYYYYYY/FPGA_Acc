"""Describe criticality changes at the last legal routing iteration."""
import csv
import hashlib
import json
from pathlib import Path
from audit_rr_experiments import audit

root=Path(__file__).resolve().parents[1];files=[Path(__file__)]
def rows(path):
    files.append(path)
    with path.open() as stream:return {int(r['task_id']):r for r in csv.DictReader(stream)}
cases=[]
for name,directory in [('zero','rr_pair_ex5p_tree_seed_zero_v1_20261014'),
                       ('midpoint','rr_pair_ex5p_tree_seed_midpoint_v1_20261014'),
                       ('full','rr_pair_ex5p_cleanup_disabled_control_v1_20261014')]:
    pair=root/'work'/directory;manifest_path=pair/'pair.json';files.append(manifest_path)
    verified=audit(manifest_path)['modes']['downstream_bounded']
    manifest=json.loads(manifest_path.read_text());config=manifest['configuration']
    assert verified['status']=='passed' and verified['repeats_verified']==5
    last=verified['counters']['iterations']-1;cap=config['criticality_cap_q']
    prefix=pair/'downstream_bounded_0'
    before=rows(Path(str(prefix)+f'.timing_iteration_{last}.input.csv'))
    after=rows(Path(str(prefix)+f'.timing_iteration_{last}.output.csv'))
    previous=rows(Path(str(prefix)+f'.timing_iteration_{last-1}.input.csv'))
    assert before.keys()==after.keys()==previous.keys()
    joined=[]
    for task in before:
        old=int(before[task]['criticality_q']);new=min(cap,int(after[task]['criticality_q']))
        assert old<=cap and int(before[task]['routed'])==1
        if old<cap and new==cap:
            joined.append(dict(task_id=task,net_id=int(before[task]['net_id']),
                previous_criticality_q=old,final_raw_criticality_q=int(after[task]['criticality_q']),
                previous_local_delay_ps=int(previous[task]['delay_ps']),
                final_local_delay_ps=int(before[task]['delay_ps'])))
    joined.sort(key=lambda r:(-(r['final_local_delay_ps']-r['previous_local_delay_ps']),r['task_id']))
    cases.append(dict(name=name,weight=config['route_tree_timing_weight_q'],last_iteration=last,
        changed_criticalities=sum(int(before[t]['criticality_q'])!=min(cap,int(after[t]['criticality_q'])) for t in before),
        newly_capped_connections=joined,
        left_cap=sum(int(before[t]['criticality_q'])==cap and int(after[t]['criticality_q'])<cap for t in before),
        native_qor=verified['native_qor']))
report=dict(status='audited_final_timing_feedback_profiled',cases=cases,
            source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            scope='Final legal iteration pre/post-STA criticality changes on development cases. Local delay columns come from iteration timing inputs. New criticality at termination does not prove a bug or that further rerouting improves QoR; minimum-iteration changes alter earlier trajectories too.',
            research_complete=False,board_result=False)
output=root/'work/rr_final_timing_feedback_profile_20261014.json';assert not output.exists()
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps([dict(name=r['name'],changed=r['changed_criticalities'],newly_capped=len(r['newly_capped_connections']),top=r['newly_capped_connections'][:2]) for r in cases]))
