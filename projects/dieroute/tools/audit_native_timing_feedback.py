#!/usr/bin/env python3
"""Independently verify timing decisions, restored trees and complete ownership."""
import argparse
from collections import defaultdict
import csv
from decimal import Decimal
import json
import mmap
from pathlib import Path
import shutil
import struct
from run_native_case import sha256
from audit_native_owner import verify_owner_usage


def read_state(directory,repeat=0):
    trees=defaultdict(dict);uses={};empty=set()
    for row in csv.DictReader((directory/'trees.csv').open()):
        r={k:int(v) for k,v in row.items()}
        if r['repeat']!=repeat:continue
        net,node=r['net'],r['node'];assert node not in trees[net]
        trees[net][node]=(r['parent'],r['pip_key'],r['depth'])
    for row in csv.DictReader((directory/'usage.csv').open()):
        r={k:int(v) for k,v in row.items()}
        if r['repeat']!=repeat:continue
        node,net=r['node'],r['net'];value=uses.setdefault(node,[r['history'],r['version'],set()])
        assert value[:2]==[r['history'],r['version']]
        if net==0xffffffff:assert node not in empty and not value[2];empty.add(node)
        else:assert node not in empty and net not in value[2];value[2].add(net)
    return dict(trees),uses


def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('run','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();run=a.run.resolve();out=a.output.resolve();rm=json.loads((run/'manifest.json').read_text())
    assert rm['status']=='passed' and rm['inputs_unchanged']
    inputs=dict(rm['inputs']);inputs[str(run/'manifest.json')]=sha256(run/'manifest.json')
    inputs.update({str(run/name):digest for name,digest in rm['artifacts'].items()})
    for path,digest in inputs.items():assert sha256(path)==digest,path
    steps={r['name']:r for r in rm['steps']};assert set(steps)=={'prepared','zero_floor','hold20','setup1434'}
    command=steps['prepared']['command'];graph,search,fp,mapping=map(Path,command[1:5]);route=Path(command[6])
    partitioned=int(command[12]) if len(command)==13 else 0;assert partitioned in (0,1)
    for step in steps.values():
        cmd=step['command'];assert len(cmd) in (12,13) and (int(cmd[12]) if len(cmd)==13 else 0)==partitioned
    baseline,before=read_state(run/'prepared/baseline');proposal,proposed=read_state(run/'prepared/proposal')
    assert (proposal,proposed)==read_state(route)
    selection=list(csv.DictReader((route/'selection.csv').open()));roots={};sinks=defaultdict(set)
    for r in selection:
        net,src,dst=int(r['net']),int(r['source']),int(r['sink'])
        assert net not in roots or roots[net]==src;roots[net]=src;sinks[net].add(dst)
    streams=[];maps=[]
    def mapped(path):
        f=path.open('rb');streams.append(f);m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);maps.append(m);return m
    raw_nets=mapped(fp/'nets.bin');raw_pips=mapped(fp/'pips.bin');native_pips=mapped(graph/'pips.bin')
    nm=mapped(mapping/'footprint_node_map.bin');pm=mapped(mapping/'footprint_pip_map.bin')
    owners=mapped(fp/'owners.bin');mask=mapped(search/'node_protection.bin');exclusive=mapped(search/'exclusive_net.bin')
    count=(len(mask)-64);frozen=bytearray((count+7)//8)
    def node(old):return struct.unpack_from('<I',nm,old*4)[0]
    for old,net in struct.iter_unpack('<II',owners):
        if net not in roots:
            n=node(old);assert n<count;frozen[n//8]|=1<<(n%8)
    assert baseline.keys()==proposal.keys()==roots.keys()
    # Original PIP parent relation independently reconstructed from the source
    # footprint. Strict depths are checked separately below.
    for net,src in roots.items():
        record=struct.unpack_from('<16I',raw_nets,net*64);assert record[0]==0
        expected={src:(0xffffffff,0xffffffff)}
        for i in range(record[5],record[5]+record[6]):
            r=struct.unpack_from('<8I',raw_pips,i*32);assert r[0]==net
            reverse=r[7]&1;parent,dst=[node(n) for n in (r[1:3][::-1] if reverse else r[1:3])]
            key=struct.unpack_from('<I',pm,i*4)[0]*2+reverse;assert dst not in expected;expected[dst]=(parent,key)
        assert {n:v[:2] for n,v in baseline[net].items()}==expected
    def verify_state(trees,uses):
        assert trees.keys()==roots.keys();expected=defaultdict(set);pips=0
        for net,tree in trees.items():
            assert tree[roots[net]]==(0xffffffff,0xffffffff,0) and sinks[net]<=tree.keys()
            parents={v[0] for v in tree.values()};assert (tree.keys()-parents-{roots[net]})<=sinks[net]
            for n,(parent,key,depth) in tree.items():
                assert n<count and mask[64+n]==0 and not frozen[n//8]&(1<<(n%8))
                assert struct.unpack_from('<I',exclusive,64+n*4)[0] in (0xffffffff,net)
                expected[n].add(net)
                if n==roots[net]:continue
                assert parent in tree and depth==tree[parent][2]+1 and depth<=0xffffffff
                pid,reverse=key>>1,key&1;r=struct.unpack_from('<8I',native_pips,pid*32)
                assert r[0]==pid and (r[7]&2 or reverse==r[7]&1)
                assert tuple(r[1:3][::-1] if reverse else r[1:3])==(parent,n);pips+=1
        assert all(len(nets)==1 for nets in expected.values())
        assert {n:u[2] for n,u in uses.items() if u[2]}==dict(expected)
        assert all(0<=u[0]<2**64-1 and 0<u[1]<2**64 for u in uses.values())
        return pips
    baseline_pips=verify_state(baseline,before);proposal_pips=verify_state(proposal,proposed)
    assert all(u[0]==0 and u[1]==1 for u in before.values())
    timing_path,=[Path(path) for path in inputs if path.endswith('/load_paths.json')]
    observations=json.loads(timing_path.read_text());results={}
    for name,setup,hold in (('zero_floor',0,0),('hold20',0,20),('setup1434',1434,0)):
        decision=json.loads((run/name/'decision.json').read_text());violations=defaultdict(int);nets=set();unconstrained=0
        for row in observations:
            assert row['original_status']==row['routed_status']
            if row['routed_status']=='reported_unconstrained_path':unconstrained+=1;continue
            assert row['routed_status']=='constrained_path';floor=setup if row['kind']=='max' else hold
            assert Decimal(row['original']['SLACK'])*1000>=floor
            if Decimal(row['routed']['SLACK'])*1000<floor:violations[row['kind']]+=1;nets.add(row['net_id'])
        assert decision['violating_nets']==sorted(nets)
        assert decision['setup_violations']==violations['max'] and decision['hold_violations']==violations['min']
        assert decision['reported_unconstrained']==unconstrained
        assert decision['selected_scope_accepted']==(not nets) and decision['authority_epoch']==(0 if nets else 1)
        assert decision['repair_requires_native_timing']==bool(nets)
        assert decision['reason']==('slack_floor' if nets else 'selected_scope_pass')
        authority,authority_use=read_state(run/name/'authority');candidate,candidate_use=read_state(run/name/'candidate')
        assert (authority,authority_use)==((baseline,before) if nets else (proposal,proposed))
        restored=set(decision['restored_nets']);assert len(restored)==len(decision['restored_nets']) and nets<=restored<=roots.keys()
        # Necessary closure condition, plus witness reachability forbids adding
        # unrelated restoration nets to make the candidate trivially pass.
        closure=set(nets)
        while True:
            expanded=closure|{owner for net in closure for n in baseline[net] for owner in proposed.get(n,[0,0,set()])[2]}
            if expanded==closure:break
            closure=expanded
        assert restored==closure
        assert candidate=={net:(baseline if net in restored else proposal)[net] for net in roots}
        # Each nonroot removal/addition increments the existing resource version
        # exactly once; history never changes during this repair operation.
        expected_use={n:[h,v,set(owners)] for n,(h,v,owners) in proposed.items()}
        for net in restored:
            for n in proposal[net]:
                if n!=roots[net]:expected_use[n][1]+=1;expected_use[n][2].remove(net)
        for net in restored:
            for n in baseline[net]:
                if n!=roots[net]:
                    value=expected_use.setdefault(n,[0,0,set()]);value[1]+=1;value[2].add(net)
        assert candidate_use==expected_use
        pips=verify_state(candidate,candidate_use)
        results[name]=dict(decision=decision,tree_pips=pips,restored_nets=sorted(restored),
                           candidate_trees_sha256=sha256(run/name/'candidate/trees.csv'),
                           candidate_usage_sha256=sha256(run/name/'candidate/usage.csv'),
                           tasks=len(selection),selected_nets=len(roots))
    inventory_results={};nodes=mapped(graph/'nodes.bin')
    for name in steps:
        for phase in ('baseline','proposal') if name=='prepared' else ('baseline','proposal','authority','candidate'):
            directory=run/name/phase;has_inventory=(directory/'owner_usage.csv').exists()
            assert has_inventory or not partitioned
            if has_inventory:inventory_results[name+'/'+phase]=verify_owner_usage(directory,nodes,partitioned,1)
    for m in maps:m.close()
    for f in streams:f.close()
    for path,digest in inputs.items():assert sha256(path)==digest,path
    out.mkdir(parents=True,exist_ok=False);shutil.copy2(__file__,out/'auditor.py')
    shutil.copy2(Path(__file__).with_name('audit_native_owner.py'),out/'audit_native_owner.py')
    result=dict(owner_inventories=inventory_results,schema='dieroute.native_timing_feedback_audit.v1',passed=True,inputs=inputs,inputs_unchanged=True,
                baseline_pips=baseline_pips,proposal_pips=proposal_pips,cases=results,board_result=False,
                native_design_legal=None,scope='Independent original/proposed/repaired native PIPs, complete task trees, exclusive ownership, exact history/version transitions and timing-policy decisions',
                limits=['Repaired candidates still require new DCP serialization and full native checks including timing.',
                        'Passing selected-load zero floors does not establish global timing, joint QoR or hardware performance.'])
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))


if __name__=='__main__':main()
