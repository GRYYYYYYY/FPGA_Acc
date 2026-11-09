#!/usr/bin/env python3
"""Freeze full-design noncore access analysis from previously verified native data."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from run_native_case import sha256

def main():
    if not __debug__:raise RuntimeError('audit requires Python assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('policy_run','analyzer','output'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=p.parse_args();run=args.policy_run.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rm=json.loads((run/'manifest.json').read_text());assert rm['status']=='passed' and rm['inputs_unchanged']
    graph,mapping,footprint=map(Path,rm['command'][1:4]);arch=rm['architecture_sha256'][:32]
    gm=json.loads((graph.parent/'manifest.json').read_text());fm=json.loads((footprint.parent/'manifest.json').read_text())
    inputs={k:v for k,v in rm['inputs'].items() if Path(k).name in ('nodes.bin','pips.bin','pins.bin','nets.bin','footprint_node_map.bin','footprint_pip_map.bin')}
    inputs[str(graph/'tiles.csv')]=gm['artifacts']['graph/tiles.csv'];inputs[str(footprint/'owners.bin')]=fm['artifacts']['footprint/owners.bin']
    parents={**rm['parent_manifests'],str(run/'manifest.json'):sha256(run/'manifest.json')}
    for path,h in parents.items():assert sha256(path)==h,path
    for name in (Path(__file__).name,'run_native_case.py','analyze_native_access.cpp'):shutil.copy2(Path(__file__).with_name(name),out/name)
    shutil.copy2(Path(__file__).parent.parent/'include/native_csr_io.hpp',out/'native_csr_io.hpp');shutil.copy2(args.analyzer,out/'analyze_native_access')
    references={}
    for name in ('rwroute/RouteNodeGraph.java','util/Utils.java','rwroute/RouterHelper.java'):
        path=Path('../persistroute/third_party/cufr/src/com/xilinx/rapidwright')/name;references[str(path.resolve())]=sha256(path)
    command=[str(out/'analyze_native_access'),str(graph),str(mapping),str(footprint),arch,str(out/'access')]
    record={'schema':'dieroute.native_access_run.v1','status':'running','started_ns':time.time_ns(),'inputs':inputs,'parent_manifests':parents,
            'architecture_sha256':rm['architecture_sha256'],'reference_sources':references,'command':command,
            'source_sha256':{f.name:sha256(f) for f in out.iterdir() if f.is_file()}}
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,h in inputs.items():assert sha256(path)==h,path
        with (out/'analyze.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        assert record['returncode']==0,'native access analysis failed'
        for path,h in {**inputs,**parents,**references}.items():assert sha256(path)==h,path
        record.update(status='passed',inputs_unchanged=True)
    except Exception as exc:record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in sorted(out.rglob('*')) if f.is_file() and f!=manifest};save()
    print(json.dumps({'manifest':str(manifest),'status':record['status']}))

if __name__=='__main__':main()
