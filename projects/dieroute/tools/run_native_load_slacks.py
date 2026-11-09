#!/usr/bin/env python3
"""Archive min/max constrained timing paths through a frozen native load set."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native-run','pin-run','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--query-script',type=Path,help='Replay an explicitly frozen query script for exact paired comparisons')
    a=p.parse_args();parent=a.native_run.resolve();pins=a.pin_run.resolve();out=a.output.resolve()
    pm=json.loads((parent/'manifest.json').read_text());pinm=json.loads((pins/'manifest.json').read_text())
    assert pm['status']=='reports_generated' and pm['returncode']==0
    assert pinm['status']=='passed' and pinm['inputs_unchanged']
    inputs={str(parent/'manifest.json'):sha256(parent/'manifest.json'),pm['input']:pm['input_sha256'],
            str(pins/'manifest.json'):sha256(pins/'manifest.json'),str(pins/'load_pins.tsv'):pinm['artifacts']['load_pins.tsv'],
            **pm.get('dependencies',{})}
    loader=parent/'checkpoint_load.tcl'
    if loader.exists():inputs[str(loader)]=pm['artifacts']['checkpoint_load.tcl']
    query=a.query_script.resolve() if a.query_script else Path(__file__).with_name('check_native_load_slacks.tcl')
    inputs[str(query)]=sha256(query)
    for path,digest in inputs.items():assert sha256(path)==digest,path
    vivado=shutil.which('vivado');assert vivado,'source Xilinx settings64.sh'
    out.mkdir(parents=True,exist_ok=False)
    for name in ('run_native_load_slacks.py','run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name),out/name)
    shutil.copy2(query,out/'check_native_load_slacks.tcl')
    shutil.copy2(pins/'load_pins.tsv',out/'load_pins.tsv')
    if loader.exists():shutil.copy2(loader,out/'checkpoint_load.tcl')
    command=[vivado,'-mode','batch','-source',str(out/'check_native_load_slacks.tcl'),'-tclargs',pm['input'],
             str(out/'checkpoint_load.tcl') if loader.exists() else '-',str(out/'load_pins.tsv'),str(out/'reports')]
    record=dict(schema='dieroute.native_load_slacks.v1',status='running',inputs=inputs,command=command,cwd=str(out),
                started_ns=time.time_ns(),board_result=False,changes_routes=False)
    manifest=out/'manifest.json'
    def save():
        temp=out/'manifest.tmp';temp.write_text(json.dumps(record,indent=2)+'\n');temp.replace(manifest)
    save()
    try:
        with (out/'console.log').open('w') as log:
            proc=subprocess.Popen(command,cwd=out,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save()
            record['returncode']=proc.wait()
        assert record['returncode']==0,'native load timing failed'
        for path,digest in inputs.items():assert sha256(path)==digest,path
        assert 'queries_failed=0\n' in (out/'reports/completed.txt').read_text()
        record.update(status='reports_generated',inputs_unchanged=True)
    except Exception as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns()
        record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps(dict(status=record['status'],manifest=str(manifest))))


if __name__=='__main__':
    main()
