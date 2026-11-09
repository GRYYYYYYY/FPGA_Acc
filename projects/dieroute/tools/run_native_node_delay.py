#!/usr/bin/env python3
"""Freeze the installed SDK nominal node approximation on audited cohort trees."""
import argparse
import csv
import json
import mmap
import os
from pathlib import Path
import shutil
import struct
import subprocess
import time
from audit_native_timing_feedback import read_state
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('feedback-run','feedback-audit','jdk','cufr','runtime','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();feedback=a.feedback_run.resolve();out=a.output.resolve()
    fm=json.loads((feedback/'manifest.json').read_text());fa=json.loads((a.feedback_audit/'audit.json').read_text())
    assert fm['status']=='passed' and fm['inputs_unchanged'] and fa['passed']
    assert fa['inputs'][str(feedback/'manifest.json')]==sha256(feedback/'manifest.json')
    command=next(s for s in fm['steps'] if s['name']=='prepared')['command'];graph=Path(command[1])
    gm=json.loads((graph.parent/'manifest.json').read_text());assert gm['status']=='passed' and gm['dependencies_unchanged']
    assert gm['runtime']==str(a.runtime.resolve())
    inputs={str(feedback/'manifest.json'):sha256(feedback/'manifest.json'),
            str(a.feedback_audit.resolve()/'audit.json'):sha256(a.feedback_audit/'audit.json'),
            str(graph.parent/'manifest.json'):fm['inputs'][str(graph.parent/'manifest.json')],
            str(graph/'nodes.bin'):fm['inputs'][str(graph/'nodes.bin')],str(graph/'tiles.csv'):gm['artifacts']['graph/tiles.csv']}
    node_ids=set()
    for label in ('baseline','proposal'):
        directory=feedback/'prepared'/label
        for name in ('trees.csv','usage.csv'):inputs[str(directory/name)]=fm['artifacts'][str((directory/name).relative_to(feedback))]
        for tree in read_state(directory)[0].values():node_ids.update(tree)
    sdk={**gm['jars'],**gm['classpath_classes'],**gm['runtime_data']}
    timing_directory=a.cufr.resolve()/'timing'
    assert (timing_directory/'ultrascaleplus/intersite_delay_terms.txt').is_file()
    sdk.update({str(f):sha256(f) for f in timing_directory.rglob('*') if f.is_file()})
    assert set(gm['jars'])=={str(f) for f in (a.cufr.resolve()/'jars').glob('*.jar')}
    assert set(gm['classpath_classes'])=={str(f) for f in (a.cufr.resolve()/'bin').rglob('*.class')}
    for path,digest in {**inputs,**sdk}.items():assert sha256(path)==digest,path
    out.mkdir(parents=True,exist_ok=False);(out/'classes').mkdir()
    runtime=out/'runtime';runtime.mkdir()
    (runtime/'data').symlink_to((a.runtime.resolve()/'data').resolve(),target_is_directory=True)
    shutil.copytree(timing_directory,runtime/'timing')
    for name in ('NativeNodeDelay.java','run_native_node_delay.py','audit_native_timing_feedback.py','run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name),out/name)
    tiles={int(r['address']):r['name'] for r in csv.DictReader((graph/'tiles.csv').open())}
    with (graph/'nodes.bin').open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as raw,(out/'nodes.tsv').open('w') as stream:
        w=csv.writer(stream,delimiter='\t',lineterminator='\n');w.writerow(('node','tile','wire','intent','membership'))
        for node in sorted(node_ids):
            r=struct.unpack_from('<16I',raw,node*64);assert r[0]==node
            w.writerow((node,tiles[r[3]],r[4],r[7],r[5]))
    cp=str(a.cufr.resolve()/'bin')+':'+str(a.cufr.resolve()/'jars/*')
    commands=[
        [str(a.jdk.resolve()/'bin/javac'),'-cp',cp,'-d',str(out/'classes'),str(out/'NativeNodeDelay.java')],
        [str(a.jdk.resolve()/'bin/java'),'-Xmx12g','-XX:ActiveProcessorCount=4','-cp',str(out/'classes')+':'+cp,
         'NativeNodeDelay',gm['device'],str(out/'nodes.tsv'),str(out/'export')]]
    record=dict(schema='dieroute.native_node_delay_export.v1',status='running',inputs=inputs,sdk=sdk,commands=commands,
                cwd=str(out),runtime=str(runtime),base_runtime=str(a.runtime.resolve()),nodes=len(node_ids),started_ns=time.time_ns(),steps=[],
                board_result=False,changes_routes=False,calibrated_corner_model=False)
    manifest=out/'manifest.json'
    def save():
        temp=out/'manifest.tmp';temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(manifest)
    save()
    try:
        env=dict(os.environ,RAPIDWRIGHT_PATH=str(runtime),RW_AUTO_GENERATE_READABLE_EDIF='0')
        for name,command in zip(('compile','export'),commands):
            with (out/(name+'.log')).open('w') as log:
                proc=subprocess.Popen(command,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
                step=dict(name=name,pid=proc.pid);record['steps'].append(step);save();step['returncode']=proc.wait();save()
                assert step['returncode']==0,name
        rows=list(csv.DictReader((out/'export/node_delays.tsv').open(),delimiter='\t'))
        assert len(rows)==len(node_ids) and {int(r['node']) for r in rows}==node_ids
        assert 'routes_changed=false\n' in (out/'export/completed.txt').read_text()
        for path,digest in {**inputs,**sdk}.items():assert sha256(path)==digest,path
        record.update(status='passed',inputs_unchanged=True,sdk_unchanged=True)
    except Exception as exc:record.update(status='failed',error=repr(exc));raise
    finally:
        record.update(finished_ns=time.time_ns(),artifacts={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest});save()
    print(json.dumps(dict(status=record['status'],nodes=len(node_ids),manifest=str(manifest))))


if __name__=='__main__':main()
