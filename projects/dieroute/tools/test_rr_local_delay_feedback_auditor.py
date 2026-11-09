"""Check pending/feedback replay against consistently rehashed corrupt fixtures."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('variant',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();variant=a.variant.resolve();out=a.output.resolve();out.mkdir(exist_ok=False)
    protocol=json.loads((variant/'protocol.json').read_text());original=Path(protocol['commands'][2][4])
    original_manifest=json.loads((original/'pair.json').read_text());assert original_manifest['status']=='completed'
    assert original_manifest['configuration']['feedback_local_delay_guard'] is True
    mode='downstream_bounded';assert set(original_manifest['modes'])=={mode}
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    originals={str(original/f'{mode}_{i}.{ext}'):digest for i,hashes in enumerate(original_manifest['modes'][mode]['hashes']) for ext,digest in hashes.items()}
    assert all(sha(Path(path))==digest for path,digest in originals.items())
    def read(path):
        with path.open() as stream:
            reader=csv.DictReader(stream);return reader.fieldnames,list(reader)
    pending_fields,pending=read(original/f'{mode}_0.pending_nets.csv')
    feedback_fields,feedback=read(original/f'{mode}_0.critical_feedback.csv')
    assert not any(int(r['iteration'])==0 for r in feedback)
    input_fields,inputs=read(original/f'{mode}_0.timing_iteration_0.input.csv')
    _,first_outputs=read(original/f'{mode}_0.timing_iteration_0.output.csv')
    output_q={int(r['task_id']):int(r['criticality_q']) for r in first_outputs}
    crossing=next(r for r in inputs if int(r['criticality_q'])<64880<=output_q[int(r['task_id'])])
    variants=[('pristine',''),('pending_reason','pending_log[iteration]==pending'),
              ('duplicate_pending',"row['net_id'] not in group"),
              ('feedback_without_delay_history','feedback_log[iteration]==expected'),
              ('criticality_input',"inputs[task]['criticality_q']==previous_criticality[task]")]
    cases=[];root_auditor=variant/'audit_tools/audit_rr_experiments.py';auditor=variant/'audit_tools/audit_rr_local_delay_feedback.py'
    for name,guard in variants:
        base=out/name;base.mkdir()
        for child in original.iterdir():
            if child.name!='pair.json':(base/child.name).symlink_to(child,target_is_directory=child.is_dir())
        manifest=json.loads(json.dumps(original_manifest));suffix=None;rows=None;fields=None
        if name=='pending_reason':
            suffix='pending_nets.csv';fields=pending_fields;rows=[dict(r) for r in pending];rows[0]['reasons']='8'
        elif name=='duplicate_pending':
            suffix='pending_nets.csv';fields=pending_fields;rows=[dict(pending[0]),*[dict(r) for r in pending]]
        elif name=='feedback_without_delay_history':
            suffix='critical_feedback.csv';fields=feedback_fields
            rows=[dict(iteration=0,net_id=crossing['net_id'],task_id=crossing['task_id'],old_q=crossing['criticality_q'],new_q=64880,decision=0),*[dict(r) for r in feedback]]
        elif name=='criticality_input':
            suffix='timing_iteration_0.input.csv';fields=input_fields;rows=[dict(r) for r in inputs]
            rows[0]['criticality_q']=str(int(rows[0]['criticality_q'])+1)
        if suffix:
            for repeat in range(5):
                path=base/f'{mode}_{repeat}.{suffix}';assert path.is_symlink();path.unlink()
                with path.open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
                if suffix in manifest['modes'][mode]['hashes'][repeat]:manifest['modes'][mode]['hashes'][repeat][suffix]=sha(path)
                if name=='feedback_without_delay_history':
                    metrics=base/f'{mode}_{repeat}.json';value=json.loads(metrics.read_text());metrics.unlink()
                    value['critical_feedback_events']=len(rows);metrics.write_text(json.dumps(value,indent=2)+'\n')
                    manifest['modes'][mode]['runs'][repeat]['critical_feedback_events']=len(rows)
        pair=base/'pair.json';pair.write_text(json.dumps(manifest,indent=2)+'\n')
        with (base/'root_check.log').open('w') as log:
            rc=subprocess.run(['python3',str(root_auditor),str(pair),'--output',str(base/'root_check.json')],stdout=log,stderr=subprocess.STDOUT).returncode
        assert rc==0,(name,'root checks must pass')
        output=base/'feedback_check.json';log_path=base/'feedback_check.log'
        with log_path.open('w') as log:
            rc=subprocess.run(['python3',str(auditor),str(pair),'--output',str(output)],stdout=log,stderr=subprocess.STDOUT).returncode
        if name=='pristine':assert rc==0 and output.exists()
        else:assert rc!=0 and not output.exists() and 'AssertionError' in log_path.read_text() and guard in log_path.read_text(),(name,log_path.read_text()[-1000:])
        cases.append(dict(name=name,root_checks_passed=True,replay_returncode=rc,guard=guard,manifest_sha256=sha(pair),log_sha256=sha(log_path)))
    assert all(sha(Path(path))==digest for path,digest in originals.items())
    sources=[Path(__file__),root_auditor,auditor,original/'pair.json']
    report=dict(status='pristine_and_four_guarded_pending_feedback_corruptions_checked',cases=cases,original_outputs_unchanged=True,
                source_sha256={str(path):sha(path) for path in sources},
                scope='Copied/symlinked fixtures from the completed guarded arm. Five fixture repetitions are changed consistently, recorded hashes/counters refreshed as needed. Fabricated first-epoch feedback uses an actual cap crossing but has no prior local delay history. Semantic rejection, not additional routing runs, quality or full version replay evidence.',
                board_result=False,research_complete=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(cases))))
