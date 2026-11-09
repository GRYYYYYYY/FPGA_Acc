"""Compare a source-bound VPR timing hook to archived actual routing-epoch outputs."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build_native_audit',type=Path)
    parser.add_argument('pair',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    audit_path,pair,output=[p.resolve() for p in (args.build_native_audit,args.pair,args.output)]
    proof=json.loads(audit_path.read_text())
    assert proof['status']=='five_repeat_source_bound_vpr_native_baseline_compatibility_audited'
    assert proof['numerical_and_canonical_compatibility'] and len(proof['cases'])==5
    build_audit=audit_path.parent/'build_dependency_audit.json'
    build=json.loads(build_audit.read_text())
    binary=Path(build['binary'])
    assert sha(binary)==build['binary_sha256']
    manifest=json.loads(pair.read_text())
    assert manifest['status']=='completed'
    mode,=manifest['modes']
    assert len(manifest['modes'][mode]['runs'])==5
    output.mkdir(exist_ok=False)
    original_adapter=pair.parent/'source/persistroute/tools/vpr_timing_analyzer.py'
    adapter=output/'vpr_timing_analyzer.py'
    shutil.copy2(original_adapter,adapter)
    step,=[s for s in manifest['steps'] if s['label']==f'{mode}_0']
    parameters={k:v for k,v in step['routing_environment'].items() if k.startswith('PERSISTROUTE_')}
    old_binary=Path(parameters['PERSISTROUTE_VPR_BIN'])
    assert sha(old_binary)==manifest['timing_vpr']['sha256']
    parameters['PERSISTROUTE_VPR_BIN']=str(binary)
    parameters['PERSISTROUTE_TIMING_COMMAND']=str(adapter)
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(parameters)
    epochs=manifest['modes'][mode]['runs'][0]['iterations']
    files=[Path(__file__).resolve(),audit_path,build_audit,pair,binary,old_binary,original_adapter,adapter]
    cases=[]
    for epoch in range(epochs):
        original_input=pair.parent/f'{mode}_0.timing_iteration_{epoch}.input.csv'
        expected=pair.parent/f'{mode}_0.timing_iteration_{epoch}.output.csv'
        copied_input=output/f'epoch_{epoch}.input.csv'
        target=output/f'epoch_{epoch}.output.csv'
        shutil.copy2(original_input,copied_input)
        command=[sys.executable,str(adapter),str(epoch),str(copied_input),str(target)]
        with (output/f'epoch_{epoch}.log').open('w') as log:
            subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        with target.open() as stream:
            rows=list(csv.DictReader(stream))
        assert len(rows)==manifest['modes'][mode]['runs'][0]['tasks']
        cases.append(dict(epoch=epoch,rows=len(rows),byte_equivalent=target.read_bytes()==expected.read_bytes(),
                          command=command,expected_sha256=sha(expected),actual_sha256=sha(target)))
        files.extend([original_input,expected,copied_input,target,Path(str(target)+'.vpr.log')])
    report=dict(status='source_bound_vpr_timing_hook_outputs_compared_to_archived_epochs',
                all_epoch_outputs_byte_equivalent=all(c['byte_equivalent'] for c in cases),
                epochs=cases,environment=parameters,
                source_sha256={str(p):sha(p) for p in files},
                scope='Actual source-bound VPR/Tatum hook with the frozen adapter and every first-repeat '
                      'bulk-schedule epoch input. Compares archived old-binary native criticality/delay/slack/CPD '
                      'CSV bytes. Not fresh routing, general cross-input equivalence, old binary source '
                      'identity, quality improvement or physical performance.',board_result=False,research_complete=False)
    (output/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],epochs=len(cases),all_equal=report['all_epoch_outputs_byte_equivalent'])))
