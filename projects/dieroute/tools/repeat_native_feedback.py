#!/usr/bin/env python3
"""Repeat a verified fixed-candidate C++ timing publication, comparing all files."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('verification-run','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--repeats',type=int,default=5);a=p.parse_args();assert a.repeats>=5
    parent=a.verification_run.resolve();out=a.output.resolve();pm=json.loads((parent/'manifest.json').read_text())
    assert pm['status']=='selected_scope_accepted_after_fresh_native_checks' and pm['inputs_unchanged']
    inputs=dict(pm['inputs']);inputs[str(parent/'manifest.json')]=sha256(parent/'manifest.json')
    inputs.update({str(parent/name):digest for name,digest in pm['artifacts'].items()})
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'runner.py')
    record=dict(schema='dieroute.native_feedback_repeat.v1',status='running',inputs=inputs,repeats=a.repeats,
                started_ns=time.time_ns(),runs=[],board_result=False,
                scope='Repeat exact checked candidate and native timing snapshot through C++ reconstruction, acceptance and whole-checkpoint publication; no repeat of Vivado timing or routing search')
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,digest in inputs.items():assert sha256(path)==digest,path
        expected={str(f.relative_to(parent/'evaluated')):sha256(f) for f in (parent/'evaluated').rglob('*') if f.is_file()}
        for index in range(a.repeats):
            directory=out/f'repeat_{index}';command=list(pm['command']);command[8]=str(directory)
            run=dict(index=index,command=command);record['runs'].append(run)
            with (out/f'repeat_{index}.log').open('w') as log:
                proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);run['pid']=proc.pid;save();run['returncode']=proc.wait()
            assert run['returncode']==0,'C++ repeat failed'
            actual={str(f.relative_to(directory)):sha256(f) for f in directory.rglob('*') if f.is_file()}
            assert actual==expected,'repeat authority/tree/history/version/oracle decision differs'
            run['artifacts_equal']=True;save()
        for path,digest in inputs.items():assert sha256(path)==digest,path
        record.update(status='passed',inputs_unchanged=True,compared_files_per_repeat=len(expected),all_artifacts_equal=True)
    except Exception as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps({k:record[k] for k in ('status','repeats','compared_files_per_repeat','all_artifacts_equal')}))


if __name__=='__main__':main()
