#!/usr/bin/env python3
"""Run bounded full-native CSR connectivity probes with frozen provenance."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from run_native_case import sha256

def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('search_run','independent_run','probe','output'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    p.add_argument('--max-labels',type=int,default=2000000);p.add_argument('--per-pair',type=int,default=2);p.add_argument('--repeats',type=int,default=5)
    p.add_argument('--quotient-run',type=Path)
    p.add_argument('--source-radius',action='store_true')
    args=p.parse_args();assert min(args.max_labels,args.per_pair,args.repeats)>0
    assert not args.source_radius or args.quotient_run,'source radius requires quotient'
    sr=args.search_run.resolve();sm=json.loads((sr/'manifest.json').read_text())
    independent=args.independent_run.resolve()/'manifest.json';im=json.loads(independent.read_text())
    assert sm['status']=='passed' and sm['inputs_unchanged'] and im['status']=='passed' and im['inputs_unchanged']
    assert im['parent_manifests'][str(sr/'manifest.json')]==sha256(sr/'manifest.json')
    graph,mapping,footprint=map(Path,sm['command'][1:4]);search=sr/'search'
    parents={str(sr/'manifest.json'):sha256(sr/'manifest.json'),str(independent):sha256(independent)}
    inputs={}
    for name in ('offsets.bin','arcs.bin','node_protection.bin','exclusive_net.bin'):inputs[str(search/name)]=sm['artifacts']['search/'+name]
    inputs[str(graph/'nodes.bin')]=sm['inputs'][str(graph/'nodes.bin')]
    inputs[str(mapping/'footprint_node_map.bin')]=sm['inputs'][str(mapping/'footprint_node_map.bin')]
    fp=footprint.parent/'manifest.json';fm=json.loads(fp.read_text());parents[str(fp)]=sha256(fp);inputs[str(footprint/'tasks.bin')]=fm['artifacts']['footprint/tasks.bin']
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    for name in (Path(__file__).name,'run_native_case.py','probe_native_search.cpp'):shutil.copy2(Path(__file__).with_name(name),out/name)
    for name in ('sparse_search.hpp','sparse_table.hpp','sparse_label_worker.hpp','label_packet.hpp','native_csr_io.hpp','native_quotient.hpp'):shutil.copy2(Path(__file__).parent.parent/'include'/name,out/name)
    shutil.copy2(args.probe,out/'probe')
    command=[str(out/'probe'),str(graph),str(search),str(footprint),str(mapping),sm['architecture_sha256'][:32],str(out/'probe_output'),str(args.max_labels),str(args.per_pair),str(args.repeats)]
    if args.quotient_run:
        qr=args.quotient_run.resolve();qm=json.loads((qr/'manifest.json').read_text());assert qm['status']=='passed' and qm['inputs_unchanged'] and qm['search_run']==str(sr)
        assert qm['inputs'][str(sr/'manifest.json')]==sha256(sr/'manifest.json')
        parents[str(qr/'manifest.json')]=sha256(qr/'manifest.json')
        for name in ('node_groups.bin','reverse_offsets.bin','reverse_sources.bin','groups.bin'):inputs[str(qr/'quotient'/name)]=qm['artifacts']['quotient/'+name]
        command.append(str(qr/'quotient'))
        if args.source_radius:command.append('source_radius')
    record=dict(schema='dieroute.native_sparse_probe_run.v1',status='running',started_ns=time.time_ns(),inputs=inputs,parent_manifests=parents,command=command,
                source_sha256={f.name:sha256(f) for f in out.iterdir() if f.is_file()})
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,digest in {**inputs,**parents}.items():assert sha256(path)==digest,path
        with (out/'run.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        for path,digest in {**inputs,**parents}.items():assert sha256(path)==digest,path
        record['inputs_unchanged']=True
        assert record['returncode']==0,'native connectivity probe rejected'
        record['status']='passed'
    except Exception as exc:record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps({'status':record['status'],'manifest':str(manifest)}))
if __name__=='__main__':main()
