"""Exercise actual persistent VPR FIFO requests, ordering, reset semantics and rejected frames."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
from persistent_vpr_timing import PersistentTimingSession,sha
import persistent_vpr_timing


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('build',type=Path)
    parser.add_argument('pair',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    base,pair,output=[p.resolve() for p in (args.build,args.pair,args.output)]
    output.mkdir(exist_ok=False)
    build_path=base/'build_dependency_audit.json'
    build=json.loads(build_path.read_text())
    assert build['status']=='new_frozen_vpr_sources_compiler_dependencies_and_link_inputs_audited'
    binary=Path(build['binary'])
    assert sha(binary)==build['binary_sha256']
    native_path=base/'native_compatibility_audit.json'
    native=json.loads(native_path.read_text())
    assert native['numerical_and_canonical_compatibility'] and len(native['cases'])==5
    scalar_path=base/'single_shot_compatibility/audit.json'
    scalar=json.loads(scalar_path.read_text())
    assert scalar['all_epoch_outputs_byte_equivalent']
    manifest=json.loads(pair.read_text())
    assert manifest['status']=='completed'
    mode,=manifest['modes']
    step,=[s for s in manifest['steps'] if s['label']==f'{mode}_0']
    environment={k:v for k,v in step['routing_environment'].items() if k.startswith('PERSISTROUTE_')}
    adapter=pair.parent/'source/persistroute/tools/vpr_timing_analyzer.py'
    tasks=pair.parent/'input.tasks'
    epochs=manifest['modes'][mode]['runs'][0]['iterations']
    snapshots=[]
    files=[Path(__file__).resolve(),Path(persistent_vpr_timing.__file__).resolve(),
           build_path,native_path,scalar_path,pair,binary,adapter,tasks]
    for epoch in range(epochs):
        source=pair.parent/f'{mode}_0.timing_iteration_{epoch}.input.csv'
        expected=pair.parent/f'{mode}_0.timing_iteration_{epoch}.output.csv'
        snapshots.append((epoch,source,expected))
        files.extend([source,expected])
    altered=output/'unrouted_reset.input.csv'
    with snapshots[0][1].open() as stream:
        reader=csv.DictReader(stream);fields,rows=reader.fieldnames,list(reader)
    rows[0]['routed']='0';rows[0]['delay_ps']='0'
    with altered.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    reference=output/'unrouted_reset.reference.csv'
    env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
    env.update(environment)
    env['PERSISTROUTE_VPR_BIN']=str(binary)
    with (output/'unrouted_reference.log').open('w') as log:
        subprocess.run([sys.executable,str(adapter),'0',str(altered),str(reference)],
                       env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    files.extend([altered,reference,Path(str(reference)+'.vpr.log')])
    requests=snapshots+list(reversed(snapshots))+[(0,altered,reference),snapshots[0],(0,altered,reference),snapshots[-1]]
    session=PersistentTimingSession(binary,environment,adapter,tasks,output/'valid_session')
    receipts=[]
    try:
        for index,(epoch,source,expected) in enumerate(requests):
            target=output/f'fifo_request_{index}.csv'
            receipt=session.analyze(epoch,source,target)
            assert target.read_bytes()==expected.read_bytes(),(index,epoch)
            receipt['byte_equivalent_to_fresh_process']=True
            receipt['expected_output']=str(expected)
            receipts.append(receipt)
            files.append(target)
        session.stop()
    finally:
        if not session.stopped:
            session.abort()
    negative=[]
    for name in ('wrong_sequence','malformed_frame','closed_without_stop'):
        session=PersistentTimingSession(binary,environment,adapter,tasks,output/name)
        target=output/(name+'.csv')
        try:
            if name=='wrong_sequence':
                session.write_frame(f'ANALYZE\t1\t{snapshots[0][1]}\t{target}\n')
                expected='Persistent timing request sequence mismatch'
            elif name=='malformed_frame':
                session.write_frame('ANALYZE\t0\tmissing_output_field\n')
                expected='Invalid persistent timing analysis request'
            else:
                os.close(session.request_fd);session.request_fd=None
                expected='Persistent timing request channel closed without STOP'
            code=session.process.wait()
            session.log.flush()
            text=(session.directory/'native.log').read_text()
            assert code!=0 and expected in text and not target.exists(),name
            negative.append(dict(name=name,returncode=code,no_output_published=True,
                                 log_sha256=sha(session.directory/'native.log')))
        finally:
            session.abort()
    for directory in [output/'valid_session',*[output/n for n in ('wrong_sequence','malformed_frame','closed_without_stop')]]:
        files.extend([directory/'receipts.jsonl',directory/'native.log'])
    report=dict(status='actual_persistent_fifo_order_reset_and_negative_frames_checked',
                requests=receipts,request_count=len(receipts),native_negative_fixtures=negative,
                all_outputs_byte_equivalent=True,
                source_sha256={str(p):sha(p) for p in files},
                scope='Actual initialized VPR FIFO session;all archived epochs chronological then reverse, '
                      'repeated boundary epochs and a fresh-process unrouted-reset fixture. Three separate '
                      'actual native protocol faults must exit nonzero without output. Not yet a socket '
                      'daemon/external-client online router integration,paired runtime measurement, '
                      'universal timing equivalence or physical performance.',board_result=False,research_complete=False)
    (output/'audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],requests=len(receipts),negative_cases=len(negative))))
