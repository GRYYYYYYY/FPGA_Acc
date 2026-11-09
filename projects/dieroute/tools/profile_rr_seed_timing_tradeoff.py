"""Join independently audited final native timing observations for seed ablation."""
import csv
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
files=[Path(__file__)]
def read(path):
    files.append(path);return json.loads(path.read_text())
comparison=read(root/'work/rr_tree_seed_zero_variant_20261014/tree_seed_comparison.json')
assert comparison['status']=='same_source_tree_seed_weight_pair_audited'
observations=[]
for name in ('full','zero'):
    base=root/f'work/rr_tree_seed_{name}_native_delay_20261014'
    profile=read(base/'profile.json');audit=read(base/'independent_xml_audit.json')
    assert audit['status']=='passed' and audit['connections']==1920
    assert audit['profile_sha256']==hashlib.sha256((base/'profile.json').read_bytes()).hexdigest()
    output=base/'native_output.csv';files.append(output)
    assert profile['native_output_sha256']==hashlib.sha256(output.read_bytes()).hexdigest()
    with output.open() as stream:rows={int(r['task_id']):r for r in csv.DictReader(stream)}
    assert len(rows)==1920
    observations.append(rows)
connections=root/'work/pr_reference_ex5p_20261013/connections.csv';files.append(connections)
with connections.open() as stream:tasks={int(r['id']):r for r in csv.DictReader(stream)}
old,new=observations;assert old.keys()==new.keys()==tasks.keys()
rows=[]
for task in old:
    before,after=old[task],new[task]
    rows.append(dict(task_id=task,net_id=int(tasks[task]['net_id']),
                     full_native_delay_ps=int(before['delay_ps']),zero_native_delay_ps=int(after['delay_ps']),
                     delta_ps=int(after['delay_ps'])-int(before['delay_ps']),
                     full_final_criticality_q=int(before['criticality_q']),
                     zero_final_criticality_q=int(after['criticality_q'])))
rows.sort(key=lambda r:(-r['delta_ps'],r['task_id']))
report=dict(status='paired_final_native_timing_profiled',connections=len(rows),
            slower=sum(r['delta_ps']>0 for r in rows),faster=sum(r['delta_ps']<0 for r in rows),
            equal=sum(r['delta_ps']==0 for r in rows),maximum_increase_ps=rows[0]['delta_ps'],
            outcomes={name:comparison['outcomes'][name]['downstream_bounded']['native_qor'] for name in ('full','zero')},
            rows=rows,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            scope='Final native connection delays and raw criticalities after audited routing. Final criticalities are outcomes, not in-flight routing inputs. Individual interconnect differences do not causally decompose global CPD; local-RC agreement does not calibrate other routes.',
            research_complete=False,board_result=False)
output=root/'work/rr_seed_weight_native_timing_tradeoff_20261014.json'
assert not output.exists();output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('rows','source_sha256')}))
