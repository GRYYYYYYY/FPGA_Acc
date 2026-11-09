"""Adversarial trace fixtures: refreshed hashes must not bypass semantic replay."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('variant',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();variant=args.variant.resolve();out=args.output.resolve();out.mkdir(exist_ok=False)
    protocol=json.loads((variant/'protocol.json').read_text());original=Path(protocol['commands'][0][4])
    manifest=json.loads((original/'pair.json').read_text())
    assert manifest['status']=='completed'
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    initial={str(original/f'{mode}_{i}.{ext}'):digest for mode,m in manifest['modes'].items()
             for i,hashes in enumerate(m['hashes']) for ext,digest in hashes.items()}
    assert all(sha(Path(path))==digest for path,digest in initial.items())
    auditor=variant/'audit_tools/audit_rr_attachment_trace.py'
    routing=variant/'audit_tools/audit_rr_experiments.py'
    assert set(manifest['modes'])=={'downstream_bounded'}
    mode='downstream_bounded'
    with (original/f'{mode}_0.attachments.csv').open() as stream:
        reader=csv.DictReader(stream);fields=reader.fieldnames;trace=list(reader)
    with (original/f'{mode}_0.attachment_branches.csv').open() as stream:
        reader=csv.DictReader(stream);branch_fields=reader.fieldnames;branches=list(reader)
    target=next(i for i,row in enumerate(trace) if int(row['prefix_delay_q'])>0)
    mutations=[('prefix_delay_q',target,'prefix_delay==row'),
               ('seed_cost_q',target,"row['seed_cost_q']==charge"),
               ('branch_delay_q',0,"branch_delay==row['branch_delay_q']"),
               ('tree_nodes_before',0,"len(tree)==row['tree_nodes_before']"),
               ('criticality_q',0,"row['criticality_q']==criticality"),
               ('branch_reentry',0,'assert node not in tree')]
    results=[]
    for name,index,expected_error in [('pristine',0,'')]+mutations:
        fixture=out/name;fixture.mkdir()
        for child in original.iterdir():
            if child.name!='pair.json':(fixture/child.name).symlink_to(child,target_is_directory=child.is_dir())
        changed=json.loads(json.dumps(manifest))
        if name!='pristine':
            copied=[dict(row) for row in (branches if name=='branch_reentry' else trace)]
            ext='attachment_branches.csv' if name=='branch_reentry' else 'attachments.csv'
            if name=='branch_reentry':copied[0]['node']=trace[0]['source']
            else:copied[index][name]=str(int(copied[index][name])+1)
            for repeat in range(5):
                target_file=fixture/f'{mode}_{repeat}.{ext}';assert target_file.is_symlink();target_file.unlink()
                with target_file.open('w') as stream:
                    writer=csv.DictWriter(stream,fieldnames=branch_fields if name=='branch_reentry' else fields)
                    writer.writeheader();writer.writerows(copied)
                changed['modes'][mode]['hashes'][repeat][ext]=sha(target_file)
        pair=fixture/'pair.json';pair.write_text(json.dumps(changed,indent=2)+'\n')
        with (fixture/'routing_check.log').open('w') as log:
            root_rc=subprocess.run(['python3',str(routing),str(pair),'--output',str(fixture/'routing_check.json')],stdout=log,stderr=subprocess.STDOUT).returncode
        assert root_rc==0,(name,'Root/hash check must pass before testing replay')
        log_path=fixture/'replay_check.log';output=fixture/'replay_check.json'
        with log_path.open('w') as log:
            replay_rc=subprocess.run(['python3',str(auditor),str(pair),'--output',str(output)],stdout=log,stderr=subprocess.STDOUT).returncode
        if name=='pristine':assert replay_rc==0 and output.exists()
        else:
            failure=log_path.read_text()
            assert replay_rc!=0 and not output.exists() and 'AssertionError' in failure and expected_error in failure,(name,failure[-1000:])
        results.append(dict(name=name,root_checks_passed=True,replay_returncode=replay_rc,
                            expected_guard=expected_error,fixture_manifest_sha256=sha(pair),log_sha256=sha(log_path)))
    assert all(sha(Path(path))==digest for path,digest in initial.items())
    sources=[Path(__file__),auditor,routing,original/'pair.json']
    report=dict(status='pristine_and_six_refreshed_hash_corruptions_checked',cases=results,
                original_outputs_unchanged=True,
                source_sha256={str(path):sha(path) for path in sources},
                scope='Copied/symlinked adversarial fixtures from an already audited development run. Each mutation is repeated across all five fixture traces and hashes refreshed; root checks pass, semantic replay rejects it. Not new routing runs, cohort, QoR or hardware evidence.',
                research_complete=False,board_result=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],cases=len(results))))
