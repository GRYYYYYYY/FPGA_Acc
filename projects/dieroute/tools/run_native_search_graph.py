#!/usr/bin/env python3
"""Build complete fixed-pin-access search adjacency with frozen provenance."""
import argparse,json,shutil,subprocess,time
from pathlib import Path
from run_native_case import sha256

def main():
    if not __debug__:raise RuntimeError('audit requires Python assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('access_run','builder','output'):p.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=p.parse_args();accessRun=args.access_run.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    am=json.loads((accessRun/'manifest.json').read_text());assert am['status']=='passed' and am['inputs_unchanged']
    graph,mapping,footprint=map(Path,am['command'][1:4]);access=accessRun/'access'
    policyFiles=[Path(f) for f in am['parent_manifests'] if json.loads(Path(f).read_text()).get('schema')=='dieroute.native_policy_run.v1'];assert len(policyFiles)==1
    policyRun=policyFiles[0].parent;pm=json.loads(policyFiles[0].read_text());assert pm['status']=='passed' and pm['inputs_unchanged']
    assert am['architecture_sha256']==pm['architecture_sha256'];csr=Path(pm['command'][4]);policy=policyRun/'policy'
    csrManifest=next(Path(f) for f in pm['parent_manifests'] if Path(f).parent==csr.parent);cm=json.loads(csrManifest.read_text());assert cm['status']=='passed'
    inputs={str(graph/'nodes.bin'):am['inputs'][str(graph/'nodes.bin')],str(graph/'tiles.csv'):am['inputs'][str(graph/'tiles.csv')],str(graph/'intents.csv'):pm['inputs'][str(graph/'intents.csv')]}
    for name in ('nets.bin','pips.bin'):inputs[str(footprint/name)]=am['inputs'][str(footprint/name)]
    for name in ('footprint_node_map.bin','footprint_pip_map.bin'):inputs[str(mapping/name)]=am['inputs'][str(mapping/name)]
    for name in ('offsets.bin','arcs.bin'):inputs[str(csr/name)]=cm['artifacts']['csr/'+name]
    for name in ('node_protection.bin','terminal_net.bin','pip_protection.bin'):inputs[str(policy/name)]=pm['artifacts']['policy/'+name]
    for name in ('core_nodes.bin','private_owner.bin','access_arcs.bin','nonterminal_components.csv'):inputs[str(access/name)]=am['artifacts']['access/'+name]
    parents={**am['parent_manifests'],str(accessRun/'manifest.json'):sha256(accessRun/'manifest.json')}
    for path,h in parents.items():assert sha256(path)==h,path
    for name in (Path(__file__).name,'run_native_case.py','build_native_search_graph.cpp'):shutil.copy2(Path(__file__).with_name(name),out/name)
    shutil.copy2(Path(__file__).parent.parent/'include/native_csr_io.hpp',out/'native_csr_io.hpp');shutil.copy2(args.builder,out/'build_native_search_graph')
    command=[str(out/'build_native_search_graph'),str(graph),str(mapping),str(footprint),str(csr),str(policy),str(access),am['architecture_sha256'][:32],str(out/'search')]
    record={'schema':'dieroute.native_search_graph_run.v1','status':'running','started_ns':time.time_ns(),'inputs':inputs,'parent_manifests':parents,
            'architecture_sha256':am['architecture_sha256'],'command':command,'source_sha256':{f.name:sha256(f) for f in out.iterdir() if f.is_file()}}
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    save()
    try:
        for path,h in inputs.items():assert sha256(path)==h,path
        with (out/'build.log').open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);record['pid']=proc.pid;save();record['returncode']=proc.wait()
        assert record['returncode']==0,'native search graph qualification failed'
        assert json.loads((out/'search/audit.json').read_text())['original_candidate_pips_preserved']
        for path,h in {**inputs,**parents}.items():assert sha256(path)==h,path
        record.update(status='passed',inputs_unchanged=True)
    except Exception as exc:record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns();record['artifacts']={str(f.relative_to(out)):sha256(f) for f in sorted(out.rglob('*')) if f.is_file() and f!=manifest};save()
    print(json.dumps({'manifest':str(manifest),'status':record['status']}))

if __name__=='__main__':main()
