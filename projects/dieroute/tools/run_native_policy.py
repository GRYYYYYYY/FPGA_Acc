#!/usr/bin/env python3
"""Freeze full native hard-admission masks and audit the original candidate footprint."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import time
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('audit requires Python assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('csr_run','builder','output'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=p.parse_args();run=args.csr_run.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rm=json.loads((run/'manifest.json').read_text());assert rm['status']=='passed' and rm['inputs_unchanged']
    command=rm['steps'][1]['command'];assert rm['steps'][1]['name']=='verify' and rm['steps'][1]['returncode']==0
    graph,mapping,footprint,csr=map(Path,command[1:5]);arch=command[5]
    gm=json.loads((graph.parent/'manifest.json').read_text());fm=json.loads((footprint.parent/'manifest.json').read_text())
    inputs=dict(rm['inputs'])
    for name in ('nodes.bin','pips.bin','intents.csv'):inputs[str(graph/name)]=gm['artifacts']['graph/'+name]
    for name in ('nets.bin','pins.bin','pips.bin','tasks.bin'):inputs[str(footprint/name)]=fm['artifacts']['footprint/'+name]
    inputs[str(csr/'protection.bin')]=rm['artifacts']['csr/protection.bin']
    parents={**rm['parent_manifests'],str(run/'manifest.json'):sha256(run/'manifest.json')}
    for path,h in parents.items():assert sha256(path)==h,path
    for name in (Path(__file__).name,'run_native_case.py','build_native_policy.cpp'):
        shutil.copy2(Path(__file__).with_name(name),out/name)
    for name in ('native_csr_io.hpp','routing_policy.hpp','edge_routes.hpp'):
        shutil.copy2(Path(__file__).parent.parent/'include'/name,out/name)
    shutil.copy2(args.builder,out/'build_native_policy')
    cmd=[str(out/'build_native_policy'),str(graph),str(mapping),str(footprint),str(csr),arch,str(out/'policy')]
    record={'schema':'dieroute.native_policy_run.v1','status':'running','started_ns':time.time_ns(),'inputs':inputs,
            'parent_manifests':parents,'architecture_sha256':rm['architecture_sha256'],'command':cmd,
            'builder_sha256':sha256(out/'build_native_policy'),'source_sha256':{f.name:sha256(f) for f in out.iterdir() if f.is_file()}}
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,h in inputs.items():assert sha256(path)==h,path
        with (out/'build.log').open('w') as log:
            proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        assert record['returncode']==0,'native policy audit failed'
        audit=json.loads((out/'policy/audit.json').read_text());assert audit['original_candidate_footprint_preserved']
        for path,h in {**inputs,**parents}.items():assert sha256(path)==h,path
        record.update(status='passed',inputs_unchanged=True)
    except Exception as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns()
        record['artifacts']={str(f.relative_to(out)):sha256(f) for f in sorted(out.rglob('*')) if f.is_file() and f!=manifest}
        save()
    print(json.dumps({'manifest':str(manifest),'status':record['status']}))


if __name__=='__main__':main()
