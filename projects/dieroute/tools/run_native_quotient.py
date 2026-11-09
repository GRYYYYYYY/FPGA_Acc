#!/usr/bin/env python3
"""Build and independently verify a complete native quotient lower-bound graph."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from run_native_case import sha256

def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('search_run','builder','verifier','output'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    a=p.parse_args();sr=a.search_run.resolve();sm=json.loads((sr/'manifest.json').read_text());assert sm['status']=='passed' and sm['inputs_unchanged']
    graph=Path(sm['command'][1]);search=sr/'search';out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs={str(sr/'manifest.json'):sha256(sr/'manifest.json'),str(graph/'nodes.bin'):sm['inputs'][str(graph/'nodes.bin')]}
    for name in ('offsets.bin','arcs.bin','node_protection.bin'):inputs[str(search/name)]=sm['artifacts']['search/'+name]
    for name in (Path(__file__).name,'run_native_case.py','build_native_quotient.cpp','verify_native_quotient.cpp'):shutil.copy2(Path(__file__).with_name(name),out/name)
    shutil.copy2(Path(__file__).parent.parent/'include/native_csr_io.hpp',out/'native_csr_io.hpp')
    shutil.copy2(a.builder,out/'build');shutil.copy2(a.verifier,out/'verify');arch=sm['architecture_sha256'][:32]
    commands=[('build',[str(out/'build'),str(graph),str(search),arch,str(out/'quotient')]),('verify',[str(out/'verify'),str(graph),str(search),str(out/'quotient'),arch,str(out/'independent')])]
    record=dict(schema='dieroute.native_quotient_run.v1',status='running',inputs=inputs,search_run=str(sr),started_ns=time.time_ns(),steps=[],source_sha256={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,digest in inputs.items():assert sha256(path)==digest,path
        for name,command in commands:
            step=dict(name=name,command=command);record['steps'].append(step)
            with (out/(name+'.log')).open('w') as log:
                proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);step['pid']=proc.pid;save();step['returncode']=proc.wait()
            assert step['returncode']==0,name
        assert json.loads((out/'independent/audit.json').read_text())['passed']
        for path,digest in inputs.items():assert sha256(path)==digest,path
        record.update(status='passed',inputs_unchanged=True)
    except Exception as exc:record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps({'status':record['status'],'manifest':str(manifest)}))
if __name__=='__main__':main()
