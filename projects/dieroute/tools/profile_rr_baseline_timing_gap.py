"""Measure native connection-delay changes against the frozen VPR baseline."""
import csv
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1];files=[Path(__file__)]
def read(path):files.append(path);return json.loads(path.read_text())
def native(base):
    path=base/'native_output.csv';files.append(path)
    with path.open() as stream:return {int(r['task_id']):r for r in csv.DictReader(stream)}
base=root/'work/rr_ex5p_frozen_baseline_native_timing_20261014'
record=read(base/'manifest.json')
assert record['status']=='baseline_native_timing_extracted_and_cpd_checked'
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in record['inputs'].items())
assert record['output_sha256']==hashlib.sha256((base/'native_output.csv').read_bytes()).hexdigest()
baseline=native(base);critical={t for t,r in baseline.items() if int(r['criticality_q'])>=64880}
report=dict(status='native_baseline_timing_gaps_measured',connections=len(baseline),
            baseline_critical_connections=len(critical),outcomes={})
for name in ('full','zero'):
    directory=root/f'work/rr_tree_seed_{name}_native_delay_20261014'
    audit=read(directory/'independent_xml_audit.json');profile=read(directory/'profile.json')
    assert audit['status']=='passed'
    assert audit['profile_sha256']==hashlib.sha256((directory/'profile.json').read_bytes()).hexdigest()
    assert profile['native_output_sha256']==hashlib.sha256((directory/'native_output.csv').read_bytes()).hexdigest()
    candidate=native(directory);assert candidate.keys()==baseline.keys()
    rows=[]
    for task,old in baseline.items():
        new=candidate[task]
        rows.append(dict(task_id=task,baseline_delay_ps=int(old['delay_ps']),
                         candidate_delay_ps=int(new['delay_ps']),
                         delta_ps=int(new['delay_ps'])-int(old['delay_ps']),
                         baseline_criticality_q=int(old['criticality_q']),
                         candidate_criticality_q=int(new['criticality_q'])))
    rows.sort(key=lambda r:(-r['delta_ps'],r['task_id']))
    report['outcomes'][name]=dict(slower=sum(r['delta_ps']>0 for r in rows),
        faster=sum(r['delta_ps']<0 for r in rows),equal=sum(r['delta_ps']==0 for r in rows),
        baseline_critical_slower=sum(r['task_id'] in critical and r['delta_ps']>0 for r in rows),
        maximum_delay_increase_ps=rows[0]['delta_ps'],rows=rows)
report.update(source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              scope='Descriptive native connection comparisons on development data. Critical set uses the existing64880 cap on frozen-baseline raw criticality; final candidate criticalities are outcomes. Changes are not an additive or causal decomposition of global CPD.',
              board_result=False,research_complete=False)
output=root/'work/rr_ex5p_baseline_timing_gap_20261014.json';assert not output.exists()
output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(dict(baseline_critical=len(critical),outcomes={k:{f:v for f,v in x.items() if f!='rows'} for k,x in report['outcomes'].items()})))
