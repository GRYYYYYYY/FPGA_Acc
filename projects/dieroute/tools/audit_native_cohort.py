#!/usr/bin/env python3
"""Independently verify whole-net selection, frozen resources, trees and PIPs."""
import argparse,csv,json,mmap,struct,time,shutil
from collections import defaultdict
from pathlib import Path
from run_native_case import sha256
from audit_native_owner import verify_owner_usage

def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run=a.run.resolve();rm=json.loads((run/'manifest.json').read_text());assert rm['status']=='passed' and rm['inputs_unchanged']
    assert 12<=len(rm['command'])<=25
    if len(rm['command'])==25:assert rm['command'][23:]==['2','1']
    _,graph,search,footprint,mapping,quotient,arch,routed,limit,take,iterations,repeats=rm['command'][:12]
    graph,search,footprint,mapping,routed=map(Path,(graph,search,footprint,mapping,routed));take,repeats=int(take),int(repeats)
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);inputs=dict(rm['inputs']);inputs[str(run/'manifest.json')]=sha256(run/'manifest.json')
    gm=graph.parent/'manifest.json';inputs[str(gm)]=sha256(gm);inputs[str(graph/'pips.bin')]=json.loads(gm.read_text())['artifacts']['graph/pips.bin']
    for name in ('selection.csv','iterations.csv','connections.csv','paths.csv','trees.csv','usage.csv','audit.json'):inputs[str(routed/name)]=rm['artifacts']['route/'+name]
    partitioned=int(rm['command'][19]) if len(rm['command'])>=20 else 0
    assert partitioned in (0,1)
    has_owners='route/owner_usage.csv' in rm['artifacts'];assert has_owners or not partitioned
    if has_owners:inputs[str(routed/'owner_usage.csv')]=rm['artifacts']['route/owner_usage.csv']
    auditor_sources={}
    for name in (Path(__file__).name,'audit_native_owner.py','run_native_case.py'):
        source=Path(__file__).with_name(name);shutil.copy2(source,out/name);auditor_sources[name]=sha256(source)
    for path,digest in inputs.items():assert sha256(path)==digest,path
    streams=[];maps=[]
    def mapped(path):
        f=Path(path).open('rb');streams.append(f);m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);maps.append(m);return m
    nodes=mapped(graph/'nodes.bin');native_pips=mapped(graph/'pips.bin');tasks=mapped(footprint/'tasks.bin');owners=mapped(footprint/'owners.bin');nm=mapped(mapping/'footprint_node_map.bin')
    offsets=mapped(search/'offsets.bin');arcs=mapped(search/'arcs.bin');mask=mapped(search/'node_protection.bin');exclusive=mapped(search/'exclusive_net.bin');count=len(nodes)//64
    def node(old):return struct.unpack_from('<I',nm,4*old)[0]
    pairs=defaultdict(int);selected=set();seeds=set();task_records={}
    for off in range(0,len(tasks),32):
        t=struct.unpack_from('<8I',tasks,off);assert t[0]==off//32;pair=t[4:6]
        if pairs[pair]<take:selected.add(t[1]);seeds.add(t[0])
        pairs[pair]+=1
    for off in range(0,len(tasks),32):
        t=struct.unpack_from('<8I',tasks,off)
        if t[1] in selected:task_records[t[0]]=(t[1],node(t[2]),node(t[3]))
    def rows(name):return [{k:(v if k=='status' else int(v)) for k,v in r.items()} for r in csv.DictReader((routed/name).open())]
    selection=rows('selection.csv');assert len(selection)==len(task_records)
    assert {r['task']:(r['net'],r['source'],r['sink']) for r in selection}==task_records
    assert {r['task'] for r in selection if r['selection_seed']}==seeds
    frozen=bytearray((count+7)//8)
    for old,net in struct.iter_unpack('<II',owners):
        if net not in selected:
            n=node(old);assert n<count;frozen[n//8]|=1<<(n%8)
    frozen_count=sum(x.bit_count() for x in frozen)
    def available(n):return n<count and mask[64+n]==0 and not frozen[n//8]&(1<<(n%8))
    def allowed(n,net):return available(n) and struct.unpack_from('<I',exclusive,64+n*4)[0] in (0xffffffff,net)
    roots={}
    for net,src,dst in task_records.values():
        assert allowed(src,net) and allowed(dst,net)
        assert net not in roots or roots[net]==src;roots[net]=src
    trees=defaultdict(dict);tree_rows=rows('trees.csv')
    for r in tree_rows:
        assert 0<=r['repeat']<repeats and r['net'] in selected and allowed(r['node'],r['net'])
        key=(r['repeat'],r['net']);assert r['node'] not in trees[key];trees[key][r['node']]=(r['parent'],r['pip_key'],r['depth'])
    assert set(trees)=={(rep,net) for rep in range(repeats) for net in selected}
    expected_usage=defaultdict(set);pip_edges=0
    for (rep,net),tree in trees.items():
        assert tree[roots[net]]==(0xffffffff,0xffffffff,0)
        for n,(parent,key,depth) in tree.items():
            expected_usage[(rep,n)].add(net)
            if n==roots[net]:continue
            assert parent in tree and depth==tree[parent][2]+1 and depth<=0xffffffff
            pid,reverse=key>>1,key&1;pip=struct.unpack_from('<8I',native_pips,pid*32);assert pip[0]==pid
            assert pip[7]&2 or reverse==(pip[7]&1)
            assert tuple(pip[1:3][::-1] if reverse else pip[1:3])==(parent,n)
            lo=struct.unpack_from('<Q',offsets,64+parent*8)[0];end=struct.unpack_from('<Q',offsets,64+(parent+1)*8)[0];hi=end
            while lo<hi:
                mid=(lo+hi)//2
                if struct.unpack_from('<II',arcs,64+mid*8)<(n,key):lo=mid+1
                else:hi=mid
            assert lo<end and struct.unpack_from('<II',arcs,64+lo*8)==(n,key);pip_edges+=1
    usage=rows('usage.csv');actual_usage=defaultdict(set);values={};empty=set()
    for r in usage:
        key=(r['repeat'],r['node']);assert 0<=r['repeat']<repeats and available(r['node']) and 0<r['version']<=0xffffffffffffffff and 0<=r['history']<0xffffffffffffffff
        value=(r['history'],r['version']);assert key not in values or values[key]==value;values[key]=value
        if r['net']==0xffffffff:assert key not in empty;empty.add(key)
        else:assert r['net'] not in actual_usage[key];actual_usage[key].add(r['net'])
    assert not empty.intersection(actual_usage)
    assert dict(actual_usage)==dict(expected_usage),'tree/ownership disagreement'
    paths=defaultdict(list)
    for r in rows('paths.csv'):paths[(r['repeat'],r['task'])].append(r)
    connection_rows=rows('connections.csv');assert len(connection_rows)==repeats*len(task_records);seen=set();found=defaultdict(int);cross_paths=0;occurrences=0;sinks=defaultdict(set)
    for r in connection_rows:
        rep,tid,net=r['repeat'],r['task'],r['net'];assert 0<=rep<repeats and tid in task_records and (rep,tid) not in seen;seen.add((rep,tid));expected_net,src,dst=task_records[tid];assert net==expected_net
        path=paths.pop((rep,tid),[]);assert r['status'] in ('found','budget_exhausted','hop_limited','exhausted')
        if r['status']!='found':assert not path and r['full_hops']==0;continue
        found[rep]+=1;sinks[(rep,net)].add(dst);tree=trees[(rep,net)];reverse=[];n=dst
        while n!=src:
            parent,key,depth=tree[n];reverse.append((parent,n,key));n=parent;assert len(reverse)<len(tree)
        expected=list(reversed(reverse));assert len(expected)==r['full_hops']==len(path)
        assert [(x['source'],x['destination'],x['pip_key']) for x in path]==expected
        assert [x['step'] for x in path]==list(range(len(path)));occurrences+=len(path)
        original=struct.unpack_from('<8I',tasks,tid*32)
        if original[4]!=original[5]:
            assert any((lambda m:m&(m-1))(struct.unpack_from('<I',nodes,n*64+20)[0]) for _,n,_ in expected);cross_paths+=1
    assert not paths
    for key,tree in trees.items():
        parents={v[0] for v in tree.values()};leaves=set(tree)-parents-{roots[key[1]]};assert leaves<=sinks[key],'orphan accepted branch'
    iteration_rows=rows('iterations.csv');converged=0
    for rep in range(repeats):
        history=[r for r in iteration_rows if r['repeat']==rep];assert history and [r['iteration'] for r in history]==list(range(len(history)))
        over=sum(len(nets)>1 for (r,n),nets in expected_usage.items() if r==rep)
        assert history[-1]['routed_tasks']==found[rep] and history[-1]['failed_tasks']==len(task_records)-found[rep] and history[-1]['overused_nodes']==over
        converged+=found[rep]==len(task_records) and over==0
    for dataset in (tree_rows,usage,connection_rows,iteration_rows):
        reference=[{k:v for k,v in r.items() if k!='repeat'} for r in dataset if r['repeat']==0]
        for rep in range(1,repeats):assert [{k:v for k,v in r.items() if k!='repeat'} for r in dataset if r['repeat']==rep]==reference
    report=json.loads((routed/'audit.json').read_text());assert report['selected_seed_tasks']==len(seeds) and report['selected_nets']==len(selected) and report['all_selected_net_tasks']==len(task_records)
    assert report['frozen_unselected_footprint_nodes']==frozen_count and report['electrical_model_converged_repeats']==converged and report['native_design_legal'] is None
    owner_inventory=verify_owner_usage(routed,nodes,partitioned,repeats) if has_owners else dict(unique_owner_inventory_verified=False)
    for m in maps:m.close()
    for f in streams:f.close()
    for path,digest in inputs.items():assert sha256(path)==digest,path
    result=dict(owner_inventory=owner_inventory,auditor_sources=auditor_sources,schema='dieroute.native_cohort_audit.v1',passed=True,inputs=inputs,inputs_unchanged=True,finished_ns=time.time_ns(),selected_nets=len(selected),tasks=len(task_records),repeats=repeats,
                electrical_model_converged_repeats=converged,frozen_unselected_nodes=frozen_count,tree_PIPs_resolved=pip_edges,path_PIP_occurrences=occurrences,cross_slr_paths=cross_paths,
                repeat_comparison_performed=repeats>1,repeated_trees_ownership_paths_and_counters_equal=True if repeats>1 else None,
                scope='Whole-net task closure, frozen outside ownership, directed native PIPs, complete shared-tree paths and exact distinct-net occupancy; no DCP writeback, full native design legality or timing/QoR')
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
if __name__=='__main__':main()
