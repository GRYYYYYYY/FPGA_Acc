#!/usr/bin/env python3
"""Find exact unchanged-path counterexamples to a static additive delay model.

This is a read-only metrics analysis of already audited trees. It performs no
route search, physical-state change, model fitting or held-out parameter tuning.
"""
import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path
import shutil
from audit_native_timing import read_run
from audit_native_timing_feedback import read_state
from run_native_case import sha256


def directed_path(tree,source,sink):
    result=[];seen=set()
    while sink!=source:
        assert sink not in seen and sink in tree
        seen.add(sink);parent,key,depth=tree[sink]
        assert parent in tree and tree[parent][2]+1==depth
        result.append((parent,sink,key));sink=parent
    return list(reversed(result))


def main():
    if not __debug__:raise RuntimeError('verification requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('feedback-run','feedback-audit','mapping-audit','original-timing','proposal-timing','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();fr=a.feedback_run.resolve();out=a.output.resolve()
    fm=json.loads((fr/'manifest.json').read_text());fa=json.loads((a.feedback_audit/'audit.json').read_text())
    ma=json.loads((a.mapping_audit/'audit.json').read_text())
    assert fm['status']=='passed' and fm['inputs_unchanged'] and fa['passed'] and ma['passed']
    assert fa['inputs'][str(fr/'manifest.json')]==sha256(fr/'manifest.json')
    assert fm['context']['mapping_audit_sha256']==sha256(a.mapping_audit/'audit.json')
    inputs={str(fr/'manifest.json'):sha256(fr/'manifest.json'),
            str(a.feedback_audit.resolve()/'audit.json'):sha256(a.feedback_audit/'audit.json'),
            str(a.mapping_audit.resolve()/'audit.json'):sha256(a.mapping_audit/'audit.json')}
    for label in ('baseline','proposal'):
        for name in ('trees.csv','usage.csv'):
            rel=f'prepared/{label}/{name}';inputs[str(fr/rel)]=fm['artifacts'][rel]
    cohort=Path(fm['cohort']);selection=cohort/'route/selection.csv';inputs[str(selection)]=fm['inputs'][str(selection)]
    inputs[str(a.mapping_audit.resolve()/'mapping.json')]=ma['artifacts']['mapping.json']
    for directory in (a.original_timing.resolve(),a.proposal_timing.resolve()):
        inputs[str(directory/'manifest.json')]=ma['manifests'][str(directory/'manifest.json')]
    for path,digest in inputs.items():assert sha256(path)==digest,path
    old=read_run(a.original_timing.resolve());new=read_run(a.proposal_timing.resolve())
    assert old[4].keys()==new[4].keys() and old[1]==new[1]
    # The mapping producer independently proved used-site connectivity and
    # physical site snapshots unchanged between these exact timing checkpoints.
    assert ma['original_to_routed_site_state_unchanged']
    for directory,meta in ((a.original_timing.resolve(),old[0]),(a.proposal_timing.resolve(),new[0])):
        inputs.update(meta['inputs']);inputs.update({str(directory/name):digest for name,digest in meta['artifacts'].items()})
    baseline=read_state(fr/'prepared/baseline')[0];proposal=read_state(fr/'prepared/proposal')[0]
    tasks={int(r['task']):{k:int(v) for k,v in r.items()} for r in csv.DictReader(selection.open())}
    mapped=json.loads((a.mapping_audit/'mapping.json').read_text());records=[];witnesses=[]
    unique=set();physical_same=set()
    for m in mapped:
        task=m['task']
        if task is None:continue
        net,pin=m['net_id'],m['to_pin'];assert (net,pin,task) not in unique;unique.add((net,pin,task))
        t=tasks[task];assert t['net']==net
        before=directed_path(baseline[net],t['source'],t['sink']);after=directed_path(proposal[net],t['source'],t['sink'])
        same=before==after;same_tree=baseline[net]==proposal[net]
        if same:physical_same.add(task)
        record=dict(net=net,task=task,to_pin=pin,same_directed_PIP_path=same,same_complete_net_tree=same_tree,
                    original_hops=len(before),proposal_hops=len(after))
        changed=False
        for mode in ('total','interconnect'):
            for corner in ('FAST_MIN','FAST_MAX','SLOW_MIN','SLOW_MAX'):
                b=Decimal(old[4][net,mode,pin][corner]);n=Decimal(new[4][net,mode,pin][corner]);delta=n-b
                assert b==int(b) and n==int(n)
                record[f'{mode}_{corner}_before_ps']=int(b);record[f'{mode}_{corner}_after_ps']=int(n)
                record[f'{mode}_{corner}_delta_ps']=int(delta)
                changed|=delta!=0
        record['observed_delay_changed']=bool(changed);records.append(record)
        if same and changed:
            witness=dict(record,path=[dict(source=s,destination=d,pip_key=k) for s,d,k in before],
                         original_tree_pips=len(baseline[net])-1,proposal_tree_pips=len(proposal[net])-1,
                         original_only_edges=sorted((v[0],n,v[1]) for n,v in baseline[net].items() if n not in proposal[net] or proposal[net][n][:2]!=v[:2]),
                         proposal_only_edges=sorted((v[0],n,v[1]) for n,v in proposal[net].items() if n not in baseline[net] or baseline[net][n][:2]!=v[:2]))
            witnesses.append(witness)
    assert {r['task'] for r in records}==tasks.keys()
    for path,digest in inputs.items():assert sha256(path)==digest,path
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'analyzer.py')
    with (out/'path_delay_pairs.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (out/'unchanged_path_witnesses.json').write_text(json.dumps(witnesses,indent=2)+'\n')
    result=dict(schema='dieroute.native_path_model_limits.v1',passed=True,inputs=inputs,inputs_unchanged=True,
                physical_tasks=len(tasks),mapped_load_observations=len(records),identical_directed_paths=len(physical_same),
                identical_path_loads=sum(r['same_directed_PIP_path'] for r in records),
                identical_path_changed_delay_loads=len(witnesses),
                identical_complete_tree_changed_delay_loads=sum(r['same_complete_net_tree'] and r['observed_delay_changed'] for r in records),
                witnesses=[dict(task=r['task'],net=r['net'],same_complete_net_tree=r['same_complete_net_tree'],
                                total_slow_max_delta_ps=r['total_SLOW_MAX_delta_ps'],
                                interconnect_slow_max_delta_ps=r['interconnect_SLOW_MAX_delta_ps']) for r in witnesses],
                artifacts={f.name:sha256(f) for f in out.iterdir() if f.is_file()},board_result=False,
                conclusion=('Exact equal directed PIP paths have different observed native net delays in these snapshots; a static path-only additive model cannot reproduce both observations exactly.'
                            if witnesses else 'No unchanged-path delay counterexample found in this cohort; this does not prove an additive model.'),
                limits=['This is an observed model counterexample, not a calibrated replacement model or isolated causal measurement of off-path capacitance.',
                        'Native delay report quantization and SDK serialization effects are not separated by a dedicated no-op net-delay control.',
                        'No prediction accuracy, robust hold margin, joint QoR or hardware-performance claim.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('inputs','artifacts')}))


if __name__=='__main__':main()
