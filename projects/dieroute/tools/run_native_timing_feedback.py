#!/usr/bin/env python3
"""Replay audited native timing through C++ transactional acceptance/repair.

Python validates provenance and converts observed ns to exact integer ps. All
tree reconstruction, state mutation, decisions and conflict closure are C++.
This runner produces repair candidates, not freshly timed accepted designs.
"""
import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time
from audit_native_load_slacks import read
from run_native_case import sha256


def picoseconds(value):
    ps=Decimal(value)*1000
    if not ps.is_finite() or ps!=ps.to_integral_value() or not -(2**63)<=ps<2**63:
        raise ValueError('slack is not exact signed 64-bit picoseconds')
    return int(ps)


def write_snapshot(path,identity,context,epoch,observations,load_ids):
    with path.open('x') as f:
        f.write(f'dieroute.native_timing_snapshot.v1\ncontext {context}\nepoch {epoch}\n')
        for line in identity.read_text().splitlines():f.write('T '+line+'\n')
        for key,value in sorted(observations.items()):
            net,pin,kind=key;status=value['_classification'] if value else 'no_reported_path'
            coverage={'constrained_path':'finite','reported_unconstrained_path':'unconstrained','no_reported_path':'missing'}[status]
            slack=str(picoseconds(value['SLACK'])) if coverage=='finite' else 'NA'
            f.write(f'L {load_ids[net,pin]} {net} {"setup" if kind=="max" else "hold"} {coverage} {slack}\n')
        f.write('end\n')


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('cohort','cohort-audit','mapping-audit','timing-audit','writeback','executable','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();cohort=a.cohort.resolve();route=cohort/'route'
    cm=json.loads((cohort/'manifest.json').read_text());ca=json.loads((a.cohort_audit/'audit.json').read_text())
    ma=json.loads((a.mapping_audit/'audit.json').read_text());ta=json.loads((a.timing_audit/'audit.json').read_text())
    wm=json.loads((a.writeback/'manifest.json').read_text())
    assert cm['status']=='passed' and cm['inputs_unchanged'] and ca['passed'] and ca['inputs_unchanged']
    assert ca['electrical_model_converged_repeats']==ca['repeats']
    assert ma['passed'] and ta['status']=='passed' and wm['status']=='passed' and wm['physical_reload_equal']
    assert ta['mapping_audit_sha256']==sha256(a.mapping_audit/'audit.json')
    assert ma['manifests'][str(cohort/'manifest.json')]==sha256(cohort/'manifest.json')
    assert ma['manifests'][str(a.writeback.resolve()/'manifest.json')]==sha256(a.writeback/'manifest.json')
    assert wm['inputs'][str(cohort/'manifest.json')]==sha256(cohort/'manifest.json')
    inputs={}
    def add(path,digest):
        path=str(Path(path).resolve());assert path not in inputs or inputs[path]==digest,path;inputs[path]=digest
    for directory,filename in ((cohort,'manifest.json'),(a.cohort_audit,'audit.json'),(a.mapping_audit,'audit.json'),
                               (a.timing_audit,'audit.json'),(a.writeback,'manifest.json')):
        add(directory/filename,sha256(directory/filename))
    for records in (ca['inputs'],ma['manifests'],ta['manifests']):
        for path,digest in records.items():add(path,digest)
    for name,digest in ta['artifacts'].items():add(a.timing_audit/name,digest)
    graph,search,fp,mapping=map(Path,cm['command'][1:5]);arch=cm['command'][6]
    owner_partition=int(cm['command'][19]) if len(cm['command'])>=20 else 0
    assert owner_partition in (0,1)
    if owner_partition:assert ca['owner_inventory']['unique_owner_inventory_verified'] and ca['owner_inventory']['partitioned']
    gm=json.loads((graph.parent/'manifest.json').read_text());fm=json.loads((fp.parent/'manifest.json').read_text())
    mm=json.loads((mapping.parent/'manifest.json').read_text())
    assert mm['status']=='passed'
    for directory,manifest,files,prefix in ((graph,gm,('nodes.bin','pips.bin'),'graph/'),
                                          (fp,fm,('nets.bin','pips.bin','tasks.bin','owners.bin'),'footprint/'),
                                          (mapping,mm,('footprint_node_map.bin','footprint_pip_map.bin'),'binary_audit/')):
        add(directory.parent/'manifest.json',sha256(directory.parent/'manifest.json'))
        for name in files:add(directory/name,manifest['artifacts'][prefix+name])
    # Read and recheck the raw per-load properties/report witnesses, then bind
    # them to the exact original and serialized proposal checkpoints.
    timing_runs=[Path(path).parent for path in ta['manifests']]
    original_dcp,= [path for path in fm['inputs'] if path.endswith('.dcp')]
    proposal_dcp=str(a.writeback.resolve()/'write/routed.dcp')
    timing={}
    for run in timing_runs:
        meta,observations,_=read(run)
        if original_dcp in meta['inputs']:label='baseline'
        elif proposal_dcp in meta['inputs']:label='proposal'
        else:raise AssertionError('timing DCP not bound to either input state')
        assert label not in timing;timing[label]=(meta,observations)
        for path,digest in meta['inputs'].items():add(path,digest)
        for name,digest in meta['artifacts'].items():add(run/name,digest)
    assert set(timing)=={'baseline','proposal'}
    assert timing['baseline'][0]['inputs'][original_dcp]==fm['inputs'][original_dcp]
    assert timing['proposal'][0]['inputs'][proposal_dcp]==wm['artifacts']['write/routed.dcp']
    for name in ('check_native_load_slacks.tcl','load_pins.tsv'):
        assert timing['baseline'][0]['artifacts'][name]==timing['proposal'][0]['artifacts'][name]
    assert timing['baseline'][1].keys()==timing['proposal'][1].keys()
    comparisons=json.loads((a.timing_audit/'load_paths.json').read_text())
    assert len(comparisons)==len(timing['baseline'][1])
    seen=set()
    for row in comparisons:
        key=(row['net_id'],row['to_pin'],row['kind']);assert key not in seen;seen.add(key)
        assert row['original']==timing['baseline'][1][key] and row['routed']==timing['proposal'][1][key]
    out.mkdir(parents=True,exist_ok=False);(out/'source').mkdir()
    root=Path(__file__).resolve().parent.parent
    source_names=['include/native_route_state.hpp','include/native_timing_feedback.hpp','include/native_csr_io.hpp',
                  'include/sparse_search.hpp','include/sparse_table.hpp','include/sparse_label_worker.hpp','include/label_packet.hpp','tools/native_timing_feedback.cpp','tools/run_native_timing_feedback.py',
                  'tools/audit_native_load_slacks.py','tools/audit_native_timing.py','tools/run_native_case.py',
                  'tb/native_timing_feedback_tb.cpp','CMakeLists.txt']
    for name in source_names:
        target=out/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(root/name,target)
    shutil.copy2(a.executable,out/'feedback');add(a.executable,sha256(a.executable))
    record=dict(schema='dieroute.native_timing_feedback_run.v1',status='running',inputs=inputs,started_ns=time.time_ns(),
                steps=[],board_result=False,native_design_legal=None,cohort=str(cohort),cohort_audit=str(a.cohort_audit.resolve()))
    manifest=out/'manifest.json'
    def save():
        tmp=out/'manifest.tmp';tmp.write_text(json.dumps(record,indent=2)+'\n');tmp.replace(manifest)
    def step(name,snapshot,setup,hold):
        command=[str(out/'feedback'),str(graph),str(search),str(fp),str(mapping),arch,str(route),str(snapshot),str(out/name),str(setup),str(hold),'1']
        if owner_partition:command.append('1')
        current=dict(name=name,command=command);record['steps'].append(current);save()
        with (out/(name+'.log')).open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);current['pid']=proc.pid;save();current['returncode']=proc.wait()
        save();assert current['returncode']==0,name+' failed'
    save()
    try:
        for path,digest in inputs.items():assert sha256(path)==digest,path
        step('prepared','-',0,0)
        context=dict(original_dcp_sha256=fm['inputs'][original_dcp],cohort_sha256=sha256(cohort/'manifest.json'),
                     mapping_audit_sha256=sha256(a.mapping_audit/'audit.json'),
                     query_sha256=timing['baseline'][0]['artifacts']['check_native_load_slacks.tcl'],
                     load_set_sha256=timing['baseline'][0]['artifacts']['load_pins.tsv'])
        record['context']=context;context_id=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest()
        (out/'snapshots').mkdir();loads=sorted({key[:2] for key in timing['baseline'][1]});load_ids={key:i for i,key in enumerate(loads)}
        (out/'load_ids.json').write_text(json.dumps([dict(load=i,net=net,pin=pin) for (net,pin),i in load_ids.items()],indent=2)+'\n')
        for label,epoch in (('baseline',0),('proposal',1)):
            write_snapshot(out/'snapshots'/(label+'.timing'),out/'prepared'/label/'tree_identity.txt',context_id,epoch,timing[label][1],load_ids)
        # Explicit policy ablations, not inferred implementation requirements.
        for name,setup,hold in (('zero_floor',0,0),('hold20',0,20),('setup1434',1434,0)):
            step(name,out/'snapshots',setup,hold)
        for path,digest in inputs.items():assert sha256(path)==digest,path
        record.update(status='passed',inputs_unchanged=True,loads=len(loads),queries_per_snapshot=len(timing['baseline'][1]),
                      scope='C++ selected-load timing policy replay and electrically checked repair proposals; fresh repaired-design native timing remains required')
    except Exception as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        record['finished_ns']=time.time_ns()
        record['artifacts']={str(f.relative_to(out)):sha256(f) for f in out.rglob('*') if f.is_file() and f!=manifest};save()
    print(json.dumps({k:record[k] for k in ('status','loads','queries_per_snapshot','scope')}))


if __name__=='__main__':main()
