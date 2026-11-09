#!/usr/bin/env python3
"""Replay whole-net speculative snapshots, reads, conflicts and atomic commits.
Recorded read completeness and optimal search execution are covered by C++
differential tests, not inferred from this trace. This is not a timing oracle.
"""
import argparse,csv,json,mmap,struct,time,shutil
from bisect import bisect_left
from collections import defaultdict
from contextlib import ExitStack
from pathlib import Path
from run_native_case import sha256
from audit_native_label_transport import crc64
from audit_native_persistent_shadows import PersistentShadowAudit
from audit_native_summary_hbm import SummaryEndpointAudit
NONE=(1<<32)-1

def rows(route,name):
    with (route/name).open() as stream:return [{k:int(v) for k,v in r.items()} for r in csv.DictReader(stream)]
def group(records,fields):
    out=defaultdict(list)
    for r in records:out[tuple(r[f] for f in fields)].append(r)
    return out

def verify(run,manifest):
    command=manifest['command'];assert len(command) in (22,23,24,25) and int(command[21]) in range(1,9)
    assert len(command)<24 or int(command[23]) in (0,1,2)
    assert list(map(int,command[17:21]))==[1,1,1,1] and int(command[12])==0
    workers=int(command[21]);repeats=int(command[11]);route=run/'route'
    assert len(command)<25 or command[23:]==['2','1']
    shadows=PersistentShadowAudit(route,command[:24])
    endpoint=SummaryEndpointAudit(route,command[:24])
    names=('transactions.csv','proposals.csv','proposal_paths.csv','transaction_passes.csv','conflicts.csv','accepted_work.csv')
    tables={name:rows(route,name) for name in names}
    # read_begin is an archive offset, not semantic transaction state.
    for data in tables.values():
        reference=[{k:v for k,v in row.items() if k not in ('repeat','read_begin')} for row in data if row['repeat']==0]
        for rep in range(1,repeats):assert [{k:v for k,v in row.items() if k not in ('repeat','read_begin')} for row in data if row['repeat']==rep]==reference
    key_fields=('repeat','iteration','wave','slot','attempt')
    transactions=group(tables['transactions.csv'],('repeat','iteration','wave','slot'))
    branches=group(tables['proposals.csv'],key_fields)
    paths=group(tables['proposal_paths.csv'],(*key_fields,'branch'))
    passes=group(tables['transaction_passes.csv'],key_fields)
    conflicts=group(tables['conflicts.csv'],key_fields)
    accepted_work={(r['repeat'],r['iteration']):r for r in tables['accepted_work.csv']}
    iterations=rows(route,'iterations.csv')
    selection=rows(route,'selection.csv');tasks={r['task']:r for r in selection}
    by_net=group(selection,('net',));order=[n[0] for n in sorted(by_net,key=lambda n:min(r['task'] for r in by_net[n]))]
    roots={net:by_net[(net,)][0]['source'] for net in order}
    totals=defaultdict(int);read_cursor=0;repeat_read_ranges=[]
    executions=group(rows(route,'execution.csv'),('repeat','iteration','wave'))
    overlap_peaks=[]
    with ExitStack() as stack:
        def mapped(path):
            stream=stack.enter_context(Path(path).open('rb'));return stack.enter_context(mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ))
        graph,search,footprint,mapping=map(Path,command[1:5])
        nodes=mapped(graph/'nodes.bin');pips=mapped(graph/'pips.bin');offsets=mapped(search/'offsets.bin');arcs=mapped(search/'arcs.bin')
        protection=mapped(search/'node_protection.bin');exclusive=mapped(search/'exclusive_net.bin');owners=mapped(footprint/'owners.bin');nm=mapped(mapping/'footprint_node_map.bin');native_tasks=mapped(footprint/'tasks.bin')
        count=len(nodes)//64;frozen=bytearray((count+7)//8)
        for old,net in struct.iter_unpack('<II',owners):
            if net not in roots:
                n=struct.unpack_from('<I',nm,old*4)[0];frozen[n//8]|=1<<(n%8)
        def allowed(n,net):return n<count and not protection[64+n] and not frozen[n//8]&(1<<(n%8)) and struct.unpack_from('<I',exclusive,64+n*4)[0] in (NONE,net)
        def arc_ok(a,b,key):
            assert a<count and b<count and key>>1<len(pips)//32
            pip=struct.unpack_from('<8I',pips,(key>>1)*32)
            assert pip[0]==key>>1 and (pip[7]&2 or key&1==pip[7]&1)
            assert tuple(pip[1:3][::-1] if key&1 else pip[1:3])==(a,b)
            lo=struct.unpack_from('<Q',offsets,64+a*8)[0];end=struct.unpack_from('<Q',offsets,64+(a+1)*8)[0];hi=end
            while lo<hi:
                mid=(lo+hi)//2
                if struct.unpack_from('<II',arcs,64+mid*8)<(b,key):lo=mid+1
                else:hi=mid
            assert lo<end and struct.unpack_from('<II',arcs,64+lo*8)==(b,key)
            return pip[6]
        data=mapped(route/'readsets.bin')
        magic,major,minor,kind,records,size,arch,crc,flags=struct.unpack_from('<8sHHIQQ16sQQ',data)
        assert (magic,major,minor,kind,flags)==(b'FPGAACCP',0,1,0x44520021,1)
        assert arch.hex()==command[6] and size==16*records==len(data)-64
        payload=memoryview(data)[64:];assert crc64(payload)==crc;payload.release()
        for rep in range(repeats):
            start_read=read_cursor;window=0
            shadows.start(rep,lambda n:struct.unpack_from('<I',nodes,n*64+20)[0])
            trees={net:{src:(NONE,NONE,0)} for net,src in roots.items()}
            uses={src:(frozenset([net]),0,1) for net,src in roots.items()};assert len(uses)==len(roots)
            status={task:1 for task in tasks};pending=set(order)
            epochs=[r for r in iterations if r['repeat']==rep]
            assert [r['iteration'] for r in epochs]==list(range(len(epochs)))
            for epoch,iteration in enumerate(epochs):
                assert iteration['present']==1<<epoch and iteration['pending_nets']==len(pending)
                if epoch:
                    for n,(ownerset,h,v) in list(uses.items()):
                        if len(ownerset)>1:uses[n]=(ownerset,h+len(ownerset)-1,v+1)
                    for net in pending:
                        for n in trees[net]:
                            if n!=roots[net]:
                                ownerset,h,v=uses[n];uses[n]=(ownerset-{net},h,v+1)
                        trees[net]={roots[net]:(NONE,NONE,0)}
                        for t in by_net[(net,)]:status[t['task']]=1
                epoch_work=defaultdict(int);kept_work=defaultdict(int)
                jobs=[n for n in order if n in pending]
                for begin in range(0,len(jobs),workers):
                    wave=begin//workers;batch=jobs[begin:begin+workers];base_uses=dict(uses);base_trees=dict(trees)
                    endpoint.publication((rep,epoch,wave,0),uses)
                    shadows.window(rep,epoch,wave,window,uses)
                    intervals=executions.pop((rep,epoch,wave));assert [r['slot'] for r in intervals]==list(range(len(batch)))
                    events=[]
                    for slot,r in enumerate(intervals):
                        assert r['net']==batch[slot] and 0<r['begin_ns']<=r['end_ns']
                        events.extend(((r['begin_ns'],1),(r['end_ns'],-1)))
                    active=peak=0
                    for _,delta in sorted(events,key=lambda x:(x[0],-x[1])):active+=delta;peak=max(peak,active)
                    assert active==0 and peak<=len(batch);overlap_peaks.append(peak)
                    for slot,net in enumerate(batch):
                        calls=transactions.pop((rep,epoch,wave,slot));assert [r['attempt'] for r in calls] in ([0],[0,1])
                        for attempt,tx in enumerate(calls):
                            assert tx['net']==net and tx['read_begin']==read_cursor
                            key=(rep,epoch,wave,slot,attempt)
                            endpoint.publication((rep,epoch,wave,2*(slot+1)+attempt),uses)
                            if attempt:shadows.replay(key,window,uses)
                            snapshot=base_uses if attempt==0 else dict(uses)
                            input_tree=base_trees[net] if attempt==0 else trees[net]
                            assert tx['tree_changed']==int(input_tree!=trees[net])
                            # Array keeps large sorted footprints compact; binary
                            # membership is enough for the much smaller write set.
                            from array import array
                            reads=array('I');actual_conflicts=[];previous=-1
                            for i in range(tx['reads']):
                                n,reserved,version=struct.unpack_from('<IIQ',data,64+(read_cursor+i)*16)
                                assert n>previous and reserved==0 and allowed(n,net)
                                previous=n;reads.append(n)
                                old=snapshot.get(n,(frozenset(),0,0));now=uses.get(n,(frozenset(),0,0))
                                assert version==old[2], 'read version differs from declared snapshot'
                                if old!=now:actual_conflicts.append((n,version,now[2]))
                            read_cursor+=tx['reads']
                            declared=conflicts.pop(key,[])
                            assert [(r['node'],r['snapshot_version'],r['current_version']) for r in declared]==actual_conflicts
                            assert tx['conflicts']==len(actual_conflicts)
                            shadow_stale=shadows.proposal(key,snapshot,uses,reads,tx['branches'])
                            stale=bool(actual_conflicts or tx['tree_changed'] or shadow_stale)
                            assert tx['committed']==int(not stale) and (not tx['overflow'] or stale)
                            assert attempt==0 or not stale
                            assert len(calls)==(2 if (attempt==0 and stale) else attempt+1)
                            local=dict(input_tree);local_status={t['task']:1 for t in by_net[(net,)]}
                            candidates=branches.pop(key,[]);assert [b['branch'] for b in candidates]==list(range(len(candidates)))
                            pass_rows=passes.pop(key,[]);assert len(pass_rows)==tx['passes']
                            assert [p['pass'] for p in pass_rows]==list(range(len(pass_rows)))
                            assert len(candidates)==tx['branches']
                            cursor=0;rescue=False;local_deferred=0;local_expanded=local_visits=0
                            for phase in range(len(pass_rows)+(1 if tx['overflow'] else 0)):
                                initial=len(local);failed=deferred=0
                                expected=[t for t in by_net[(net,)] if not phase or local_status[t['task']]!=0]
                                for task in expected:
                                    if cursor==len(candidates):assert tx['overflow'];break
                                    b=candidates[cursor];cursor+=1;tid=task['task']
                                    assert (b['task'],b['net'],b['sink'],b['pass'],b['rescue'])==(tid,net,task['sink'],phase,int(rescue))
                                    assert b['sink_die']==struct.unpack_from('<I',native_tasks,tid*32+20)[0]
                                    assert b['status'] in range(5) and b['deferred'] in (0,1)
                                    if phase:local_deferred+=1
                                    local_expanded+=b['expanded'];local_visits+=b['edge_visits']
                                    path=paths.pop((*key,b['branch']),[])
                                    assert [p['step'] for p in path]==list(range(len(path)))
                                    if b['status']==0:
                                        n=b['attachment'];assert n in local
                                        depth=local[n][2];cost=0
                                        for edge in path:
                                            dst=edge['destination'];assert edge['source']==n and dst not in local and allowed(dst,net)
                                            index=bisect_left(reads,dst);assert index<len(reads) and reads[index]==dst, 'write absent from complete read footprint'
                                            die=arc_ok(n,dst,edge['pip_key'])
                                            value=shadows.edge_cost(b['branch'],dst,die,1<<epoch)
                                            ownerset,h,v=snapshot.get(dst,(frozenset(),0,0));cost+=value if value is not None else 1+h+(1<<epoch)*len(ownerset-{net})
                                            depth+=1;local[dst]=(n,edge['pip_key'],depth);n=dst
                                        assert n==task['sink'] and depth==b['hops'] and cost==b['cost'] and not b['deferred']
                                    else:
                                        assert not path;failed+=1;deferred+=b['deferred']
                                    local_status[tid]=b['status']
                                if phase==len(pass_rows):assert tx['overflow'];break
                                p=pass_rows[phase];after=len(local);enter_rescue=not rescue and deferred and after==initial
                                retry=bool(failed and after>initial or enter_rescue)
                                assert (p['tree_before'],p['tree_after'],p['failed_tasks'],p['budget_deferred'],p['rescue'],p['will_retry'])==(initial,after,failed,deferred,int(rescue),int(retry))
                                assert retry==(phase+1<len(pass_rows) or bool(tx['overflow']))
                                if enter_rescue:rescue=True
                            assert cursor==len(candidates)
                            if not tx['overflow']:
                                assert (local_expanded,local_visits,local_deferred)==(tx['expanded'],tx['edge_visits'],tx['deferred_retries'])
                            else:
                                assert local_expanded<=tx['expanded'] and local_visits<=tx['edge_visits']
                            for field in ('expanded','edge_visits','quotient_expanded','quotient_edge_visits','deferred_retries'):
                                epoch_work[field]+=tx[field]
                                if tx['committed']:kept_work[field]+=tx[field]
                            epoch_work['max_labels']=max(epoch_work['max_labels'],tx['max_labels'])
                            if tx['committed']:
                                kept_work['max_labels']=max(kept_work['max_labels'],tx['max_labels'])
                                for n in local.keys()-trees[net].keys():
                                    ownerset,h,v=uses.get(n,(frozenset(),0,0));assert net not in ownerset;uses[n]=(ownerset|{net},h,v+1)
                                trees[net]=local;status.update(local_status)
                            totals['transactions']+=1;totals['replays']+=attempt;totals['conflicts']+=len(actual_conflicts)
                            totals['reads']+=tx['reads'];totals['discarded_expanded']+=tx['expanded']*(not tx['committed'])
                            totals['label_packets']+=tx['label_packets']
                    window+=1
                assert all(iteration[k]==v for k,v in epoch_work.items()), 'discarded/replayed work missing from total'
                kept=accepted_work.pop((rep,epoch));assert all(kept[k]==v for k,v in kept_work.items())
                routed=sum(v==0 for v in status.values());over=sum(len(v[0])>1 for v in uses.values())
                assert (iteration['routed_tasks'],iteration['failed_tasks'],iteration['overused_nodes'])==(routed,len(tasks)-routed,over)
                pending={tasks[t]['net'] for t,v in status.items() if v!=0}
                for ownerset,h,v in uses.values():
                    if len(ownerset)>1:pending.update(ownerset)
                if not pending:assert epoch==len(epochs)-1
            endpoint.publication((rep,NONE,window,0),uses)
            shadows.end(rep,window,uses)
            actual_trees=[r for r in rows(route,'trees.csv') if r['repeat']==rep]
            assert {(r['net'],r['node']):(r['parent'],r['pip_key'],r['depth']) for r in actual_trees}=={(net,n):v for net,tree in trees.items() for n,v in tree.items()}
            expected_uses=[(n,net,h,v) for n,(nets,h,v) in sorted(uses.items()) for net in (sorted(nets) if nets else [NONE])]
            assert [(r['node'],r['net'],r['history'],r['version']) for r in rows(route,'usage.csv') if r['repeat']==rep]==expected_uses
            repeat_read_ranges.append((start_read,read_cursor))
        assert read_cursor==records
        # All repeated sorted read IDs/versions must match byte for byte.
        import hashlib
        digests=[]
        for lo,hi in repeat_read_ranges:
            h=hashlib.sha256()
            for offset in range(64+lo*16,64+hi*16,8*1024*1024):h.update(data[offset:min(64+hi*16,offset+8*1024*1024)])
            digests.append(h.hexdigest())
        assert len(set(digests))==1
    assert not transactions and not branches and not paths and not passes and not conflicts and not executions and not accepted_work
    kernel=None
    if len(command)==25:
        from audit_native_net_commit import verify as verify_kernel
        kernel=verify_kernel(run,command)
    endpoint_result=endpoint.finish()
    if kernel:
        endpoint_result['scope']='Live endpoint commands and kernel-derived whole-net authority bound by independent replay; execution backend requires separate provenance; CPU still orchestrates search and dispatch.'
    return dict(net_commit=kernel,summary_hbm=endpoint_result,persistent_shadows=shadows.finish(),passed=True,repeats=repeats,net_workers=workers,totals=dict(totals),read_footprints_repeat_sha256=digests[0],peak_observed_overlapping_proposals=max(overlap_peaks),
                reconstructed_authority=True,read_versions_conflicts_and_fixed_commit_order_verified=True,all_speculative_and_replay_work_counted=True,
                limits='Whole-net CPU proposals overlap on immutable snapshots; commits remain serial. Recorded read/version replay is not an independent search or proof of off-path read completeness. No hardware, full-design QoR or physical latency claim.')

def main():
    if not __debug__:raise RuntimeError('audit requires assertions')
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--cohort-audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    run=a.run.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    manifest=json.loads((run/'manifest.json').read_text());cohort_path=a.cohort_audit.resolve()/'audit.json';cohort=json.loads(cohort_path.read_text())
    assert manifest['status']=='passed' and cohort['passed'] and cohort['inputs_unchanged']
    assert cohort['inputs'][str(run/'manifest.json')]==sha256(run/'manifest.json')
    inputs=dict(cohort['inputs']);inputs[str(cohort_path)]=sha256(cohort_path)
    for name,digest in manifest['artifacts'].items():inputs[str(run/name)]=digest
    sources={}
    for name in ('audit_native_parallel.py','audit_native_label_transport.py','audit_native_persistent_shadows.py','audit_native_summary_hbm.py','audit_native_owner_publish.py','audit_native_net_commit.py','audit_net_commit.py','run_native_case.py'):
        source=Path(__file__).with_name(name);sources[name]=sha256(source);shutil.copy2(source,out/name)
    for path,digest in inputs.items():assert sha256(path)==digest,path
    result=verify(run,manifest)
    for path,digest in inputs.items():assert sha256(path)==digest,path
    for name,digest in sources.items():assert sha256(out/name)==sha256(Path(__file__).with_name(name))==digest
    result.update(schema='dieroute.native_parallel_audit.v1',inputs=inputs,inputs_unchanged=True,auditor_sources=sources,finished_ns=time.time_ns(),board_result=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='inputs'}))
if __name__=='__main__':main()
