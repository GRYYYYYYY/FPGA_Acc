#!/usr/bin/env python3
"""Compare original/no-op/proposed/repaired native delay and bus-skew observations."""
import argparse
import csv
from decimal import Decimal
import json
from pathlib import Path
import shutil
from audit_native_timing import read_run,bus_comparison
from audit_native_timing_feedback import read_state
from run_native_case import sha256


def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('original','noop','proposal','repair','noop-inventory-audit','path-model-audit',
                 'feedback-run','repair-verification','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();directories={label:getattr(a,label).resolve() for label in ('original','noop','proposal','repair')}
    stages={label:read_run(path) for label,path in directories.items()};original=stages['original']
    inputs={}
    def add(path,digest):
        path=str(Path(path).resolve());assert path not in inputs or inputs[path]==digest,path;inputs[path]=digest
    for label,value in stages.items():
        directory=directories[label];meta=value[0]
        assert value[1]==original[1] and value[2]==original[2] and value[4].keys()==original[4].keys()
        assert meta['artifacts']['check_native_timing.tcl']==original[0]['artifacts']['check_native_timing.tcl']
        add(directory/'manifest.json',sha256(directory/'manifest.json'))
        for path,digest in meta['inputs'].items():add(path,digest)
        for name,digest in meta['artifacts'].items():add(directory/name,digest)
    inventory=json.loads(a.noop_inventory_audit.read_text());assert inventory['comparison']['all_inventory_equal']
    assert all(inventory['comparison']['byte_equal'].values())
    for label,section in (('original',inventory),('noop',inventory['comparison'])):
        producer=section['producer'];path=Path(producer['manifest']);assert sha256(path)==producer['manifest_sha256']
        add(path,producer['manifest_sha256']);pm=json.loads(path.read_text())
        assert pm['status']=='passed' and pm['inputs_unchanged']
        checkpoint=pm['inputs']['input'];assert stages[label][0]['inputs'][checkpoint['path']]==checkpoint['sha256']
        add(checkpoint['path'],checkpoint['sha256'])
        for name,digest in producer['hashes'].items():
            assert pm['artifacts']['inventory/'+name]==digest
            add(path.parent/'inventory'/name,digest)
    add(a.noop_inventory_audit,sha256(a.noop_inventory_audit))
    model=json.loads((a.path_model_audit/'audit.json').read_text());assert model['passed'] and model['inputs_unchanged']
    for label in ('original','proposal'):
        path=directories[label]/'manifest.json';assert model['inputs'][str(path)]==sha256(path)
    for name,digest in model['artifacts'].items():add(a.path_model_audit/name,digest)
    add(a.path_model_audit/'audit.json',sha256(a.path_model_audit/'audit.json'))
    # Bind the repair's independently checked tree to this exact native timing
    # checkpoint. A filename or matching selected-net set is insufficient.
    feedback=a.feedback_run.resolve();verification=a.repair_verification.resolve()
    fm=json.loads((feedback/'manifest.json').read_text());vm=json.loads((verification/'manifest.json').read_text())
    assert fm['status']=='passed' and fm['inputs_unchanged']
    assert vm['status']=='selected_scope_accepted_after_fresh_native_checks' and vm['inputs_unchanged']
    assert model['inputs'][str(feedback/'manifest.json')]==sha256(feedback/'manifest.json')
    assert vm['inputs'][str(feedback/'manifest.json')]==sha256(feedback/'manifest.json')
    for label in ('original','proposal'):
        path=directories[label]/'manifest.json';assert fm['inputs'][str(path)]==sha256(path)
    native_parents=[p for p in stages['repair'][0]['inputs'] if p.endswith('/manifest.json')]
    assert len(native_parents)==1
    parent=native_parents[0];assert vm['inputs'][parent]==stages['repair'][0]['inputs'][parent]
    native=json.loads(Path(parent).read_text())
    assert vm['inputs'][native['input']]==native['input_sha256']
    assert stages['repair'][0]['inputs'][native['input']]==native['input_sha256']
    for directory,meta in ((feedback,fm),(verification,vm)):
        add(directory/'manifest.json',sha256(directory/'manifest.json'))
    state_dirs={'original':feedback/'prepared/baseline','proposal':feedback/'prepared/proposal',
                'repair':verification/'evaluated/authority'}
    trees={}
    for label,directory in state_dirs.items():
        producer,meta=(verification,vm) if label=='repair' else (feedback,fm)
        for name in ('trees.csv','usage.csv'):
            path=directory/name;add(path,meta['artifacts'][str(path.relative_to(producer))])
        trees[label]=read_state(directory)[0]
        assert trees[label].keys()==original[1].keys()
    case=vm['case'];assert Path(case).name==case
    decision_path=feedback/case/'decision.json'
    add(decision_path,fm['artifacts'][str(decision_path.relative_to(feedback))])
    restored=set(json.loads(decision_path.read_text())['restored_nets']);assert restored<=trees['original'].keys()
    expected_stage={net:'original' if net in restored else 'proposal' for net in trees['repair']}
    assert all(tree==trees[expected_stage[net]][net] for net,tree in trees['repair'].items())
    trees['noop']=trees['original']
    rows=[];changes={};corners=('FAST_MIN','FAST_MAX','SLOW_MIN','SLOW_MAX')
    for key in sorted(original[4]):
        net,mode,pin=key;row=dict(net_id=net,mode=mode,to_pin=pin)
        for corner in corners:
            values={label:Decimal(stage[4][key][corner]) for label,stage in stages.items()}
            assert all(v==int(v) for v in values.values())
            for label,v in values.items():row[f'{label}_{corner}_ps']=int(v)
            for label in ('noop','proposal','repair'):row[f'{label}_minus_original_{corner}_ps']=int(values[label]-values['original'])
        rows.append(row)
    for label in ('noop','proposal','repair'):
        changes[label]={}
        for mode in ('total','interconnect'):
            changes[label][mode]={}
            for corner in corners:
                values=[r[f'{label}_minus_original_{corner}_ps'] for r in rows if r['mode']==mode]
                changes[label][mode][corner]=dict(increased=sum(v>0 for v in values),decreased=sum(v<0 for v in values),
                                                unchanged=sum(v==0 for v in values),minimum_delta_ps=min(values),maximum_delta_ps=max(values))
    witnesses=json.loads((a.path_model_audit/'unchanged_path_witnesses.json').read_text());controlled=[]
    for witness in witnesses:
        record={k:witness[k] for k in ('task','net','to_pin','same_complete_net_tree')};record['delays']={}
        for mode in ('total','interconnect'):
            record['delays'][mode]={}
            for corner in corners:
                key=(witness['net'],mode,witness['to_pin'])
                values={label:int(Decimal(stage[4][key][corner])) for label,stage in stages.items()}
                assert values['original']==witness[f'{mode}_{corner}_before_ps'] and values['proposal']==witness[f'{mode}_{corner}_after_ps']
                record['delays'][mode][corner]=values
        controlled.append(record)
    buses={label:bus_comparison(original[3],stages[label][3]) for label in ('noop','proposal','repair')}
    # Equality is an observed control, not an assumption used to fill missing
    # delays. Count all comparisons even if a later workload disproves locality.
    tree_pairs=[]
    labels=list(stages)
    for i,left in enumerate(labels):
        for right in labels[i+1:]:
            same={net for net in original[1] if trees[left][net]==trees[right][net]}
            keys=[key for key in original[4] if key[0] in same]
            changed=[dict(net=key[0],mode=key[1],to_pin=key[2]) for key in keys
                     if stages[left][4][key]!=stages[right][4][key]]
            tree_pairs.append(dict(left=left,right=right,identical_tree_nets=len(same),
                                   delay_objects=len(keys),changed_delay_objects=changed))
    repair_mismatches=[dict(net=key[0],mode=key[1],to_pin=key[2]) for key in original[4]
                       if stages['repair'][4][key]!=stages[expected_stage[key[0]]][4][key]]
    for path,digest in inputs.items():assert sha256(path)==digest,path
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'auditor.py')
    with (out/'four_stage_delays.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (out/'controlled_unchanged_path_witnesses.json').write_text(json.dumps(controlled,indent=2)+'\n')
    noop_equal=all(r[f'noop_minus_original_{corner}_ps']==0 for r in rows for corner in corners)
    result=dict(schema='dieroute.native_delay_control_audit.v2',status='analyzed',inputs=inputs,inputs_unchanged=True,
                selected_nets=len(original[1]),load_pins=len(rows)//2,delay_objects_per_stage=len(rows),
                noop_physical_inventory_equal=True,noop_all_observed_delays_equal=noop_equal,
                delay_changes_vs_original=changes,bus_skew=buses,unchanged_path_witnesses=controlled,
                identical_tree_comparisons=tree_pairs,restored_nets=sorted(restored),
                repair_delays_match_their_tree_snapshot=not repair_mismatches,repair_delay_mismatches=repair_mismatches,
                repair_bus_skew_passed=buses['repair']['violations']==0,
                artifacts={f.name:sha256(f) for f in out.iterdir() if f.is_file()},board_result=False,
                limits=['The no-op control is SDK serialization of the original physical design; it does not identify an individual capacitance or timing-model parameter.',
                        'Observed delay differences are not automatically subtracted as a correction or treated as additive per-PIP costs.',
                        'No calibrated model accuracy, joint wirelength/CPD, bitstream or hardware claim follows from this analysis alone.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','noop_all_observed_delays_equal','repair_bus_skew_passed','bus_skew')}))


if __name__=='__main__':main()
