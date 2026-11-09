#!/usr/bin/env python3
"""Archive native bitstream generation for a checked routed DCP; never program a device."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from audit_dcp_reports import native_reports
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native-run','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--preload-libudev',type=Path,help='Process-local system libudev preload for a separately diagnosed allocator/deep-binding crash')
    a=p.parse_args();parent=a.native_run.resolve();out=a.output.resolve()
    report=native_reports(parent);pm=json.loads((parent/'manifest.json').read_text())
    assert report['fully_routed_without_errors'] and report['no_drc_errors_or_critical_warnings']
    assert report['timing']['wns_ns']>=0 and report['timing']['whs_ns']>=0
    inputs={str(parent/'manifest.json'):sha256(parent/'manifest.json'),pm['input']:pm['input_sha256'],**pm.get('dependencies',{})}
    loader=parent/'checkpoint_load.tcl'
    if loader.exists():inputs[str(loader)]=pm['artifacts']['checkpoint_load.tcl']
    environment=os.environ.copy();overrides={}
    if a.preload_libudev:
        library=a.preload_libudev.resolve()
        assert library.is_file() and library.name.startswith('libudev.so.1')
        assert not environment.get('LD_PRELOAD'),'refuse to replace an existing preload'
        inputs[str(library)]=sha256(library)
        overrides['LD_PRELOAD']=str(library);environment.update(overrides)
    for path,digest in inputs.items():assert sha256(path)==digest,path
    vivado=shutil.which('vivado');assert vivado,'source Xilinx settings64.sh'
    out.mkdir(parents=True,exist_ok=False)
    for name in ('check_native_bitstream.tcl','run_native_bitstream.py','audit_dcp_reports.py','run_native_case.py'):
        shutil.copy2(Path(__file__).with_name(name),out/name)
    if loader.exists():shutil.copy2(loader,out/'checkpoint_load.tcl')
    command=[vivado,'-mode','batch','-source',str(out/'check_native_bitstream.tcl'),'-tclargs',pm['input'],
             str(out/'checkpoint_load.tcl') if loader.exists() else '-',str(out/'output')]
    record=dict(schema='dieroute.native_bitstream_run.v1',status='running',inputs=inputs,command=command,cwd=str(out),
                environment_overrides=overrides,
                expected_part=report['design']['part'],started_ns=time.time_ns(),board_result=False,device_programmed=False,
                scope='Native write_bitstream on an already checked implemented DCP; no route_design or property/constraint override')
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        with (out/'console.log').open('w') as log:
            proc=subprocess.Popen(command,cwd=out,env=environment,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        assert record['returncode']==0,'write_bitstream command failed; inspect archived console'
        assert (out/'output/completed.txt').read_text()=='write_bitstream_completed=true\nroute_design_invoked=false\ndevice_programmed=false\n'
        for name in ('candidate.bit','design.txt','before_route_status.rpt','after_route_status.rpt','bitstream_drc.rpt','drc_ruledeck.txt','drc_checks.tsv','bitstreams.tsv'):
            assert (out/'output'/name).is_file() and (out/'output'/name).stat().st_size>0,name
        for path,digest in inputs.items():assert sha256(path)==digest,path
        record.update(status='bitstreams_generated',inputs_unchanged=True)
    except Exception as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps(dict(status=record['status'],manifest=str(manifest))))


if __name__=='__main__':main()
