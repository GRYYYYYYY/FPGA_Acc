#!/usr/bin/env python3
"""Join paired observed delay with original and rerouted physical path depths."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import shutil
import struct
from run_native_case import sha256


def path_depth(source,sink,parents):
    seen=set();node=sink
    while node!=source:
        assert node not in seen and node in parents,'original path disconnected/cyclic'
        seen.add(node);node=parents[node]
    return len(seen)


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('mapping-audit','cohort-run','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();ma=a.mapping_audit.resolve();cohort=a.cohort_run.resolve()
    am=json.loads((ma/'audit.json').read_text());cm=json.loads((cohort/'manifest.json').read_text())
    assert am['passed'] and cm['status']=='passed' and cm['inputs_unchanged']
    assert am['manifests'][str(cohort/'manifest.json')]==sha256(cohort/'manifest.json')
    for name,digest in am['artifacts'].items():assert sha256(ma/name)==digest,name
    fp=Path(cm['command'][3]);fm=json.loads((fp.parent/'manifest.json').read_text());inputs={}
    assert cm['inputs'][str(fp.parent/'manifest.json')]==sha256(fp.parent/'manifest.json')
    for name in ('nets.bin','pips.bin','tasks.bin'):
        digest=fm['artifacts']['footprint/'+name];assert sha256(fp/name)==digest
        inputs[str(fp/name)]=digest
    for name in ('selection.csv','connections.csv','paths.csv'):
        digest=cm['artifacts']['route/'+name];assert sha256(cohort/'route'/name)==digest
        inputs[str(cohort/'route'/name)]=digest
    selections=list(csv.DictReader((cohort/'route/selection.csv').open()))
    tasks={};parents={};pipcounts={}
    with (fp/'tasks.bin').open('rb') as f:
        for r in selections:
            tid=int(r['task']);f.seek(tid*32);t=struct.unpack('<8I',f.read(32));assert t[0]==tid and t[1]==int(r['net'])
            tasks[tid]=t
    with (fp/'nets.bin').open('rb') as nf,(fp/'pips.bin').open('rb') as pf:
        for n in sorted({t[1] for t in tasks.values()}):
            nf.seek(n*64);net=struct.unpack('<16I',nf.read(64));assert net[0]==0
            pf.seek(net[5]*32);parents[n]={};pipcounts[n]=net[6]
            for _ in range(net[6]):
                pp=struct.unpack('<8I',pf.read(32));assert pp[0]==n
                src,dst=pp[1:3][::-1] if pp[7]&1 else pp[1:3]
                assert dst not in parents[n], 'original net is not a unique-parent tree'
                parents[n][dst]=src
    routes=defaultdict(list)
    for r in csv.DictReader((cohort/'route/paths.csv').open()):
        if r['repeat']=='0':routes[int(r['task'])].append(r)
    lengths={}
    for r in csv.DictReader((cohort/'route/connections.csv').open()):
        if r['repeat']=='0':
            tid=int(r['task']);assert r['status']=='found' and int(r['net'])==tasks[tid][1]
            path=routes[tid];assert len(path)==int(r['full_hops'])
            assert [int(e['step']) for e in path]==list(range(len(path)))
            for x,y in zip(path,path[1:]):assert x['destination']==y['source']
            t=tasks[tid];lengths[tid]=(path_depth(t[2],t[3],parents[t[1]]),len(path))
    assert lengths.keys()==tasks.keys()
    observations=list(csv.DictReader((ma/'task_delay_observations.csv').open()))
    for r in observations:
        before,after=lengths[int(r['task'])] if r['task'] else ('','')
        r.update(original_hops=before,routed_hops=after,hop_delta=after-before if r['task'] else '')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'analyzer.py')
    with (out/'path_delay_observations.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(observations[0]));w.writeheader();w.writerows(observations)
    worst=sorted((r for r in observations if r['task']),key=lambda r:int(r['SLOW_MAX_delta_ps']),reverse=True)[:10]
    result=dict(schema='dieroute.native_path_delay_diagnosis.v1',passed=True,
                mapping_audit_sha256=sha256(ma/'audit.json'),cohort_manifest_sha256=sha256(cohort/'manifest.json'),inputs=inputs,
                tasks=len(tasks),logical_loads=len(observations),worst_slow_max_increases=worst,
                decreased_hops=sum(b<a for a,b in lengths.values()),increased_hops=sum(b>a for a,b in lengths.values()),unchanged_hops=sum(b==a for a,b in lengths.values()),
                artifacts={f.name:sha256(f) for f in out.iterdir() if f.is_file()},board_result=False,
                limits=['Directed original/rerouted path-depth observations only; hops are not physical wirelength or delay.',
                        'Association with delay does not identify the causal contribution of a routing heuristic.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','worst_slow_max_increases')}))


if __name__=='__main__':main()
