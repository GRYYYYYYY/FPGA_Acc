"""Reconstruct serial commits/owner refresh/cost epochs and compare checkpoints."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import struct

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('pending_audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pair=a.manifest.resolve();base=pair.parent;proof_path=a.pending_audit.resolve()
    proof=json.loads(proof_path.read_text())
    assert proof['status']=='five_repeat_critical_feedback_pending_and_owner_replay_audited'
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in proof['source_sha256'].items())
    assert proof['source_sha256'][str(pair)]==hashlib.sha256(pair.read_bytes()).hexdigest()
    manifest=json.loads(pair.read_text());cfg=manifest['configuration']
    assert not cfg['speculative_workers'] and not cfg['cleanup_passes'] and cfg['task_order']=='preserve'
    assert cfg['cost_state_bits']==64 and cfg['timing_updates']
    header=(base/'source/persistroute/include/pathfinder.hpp').read_text()
    for text in ('present_start_q = 256','present_multiplier_q = 512','history_increment_q = 256'):
        assert text in header,'This replay covers the frozen default cost schedule only'
    files=[Path(__file__),pair,proof_path,base/'source/persistroute/include/pathfinder.hpp']
    def table(path):
        files.append(path)
        with path.open() as stream:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    def binary(path,layout):files.append(path);return list(struct.iter_unpack(layout,path.read_bytes()))
    original=binary(base/'input.resources','<HHHHII');task_rows=binary(base/'input.tasks','<IIIIHHIII')
    tasks={r[0]:dict(net=r[1],source=r[2],priority=r[6],criticality=r[4]) for r in task_rows}
    assert len(tasks)==len(task_rows)
    net_tasks=defaultdict(list);sources={}
    for task,t in tasks.items():
        net_tasks[t['net']].append(task);assert sources.setdefault(t['net'],t['source'])==t['source']
    mask=(1<<64)-1;none=0xffffffff
    def fnv_words(words):
        value=1469598103934665603
        for word in words:
            for shift in range(0,64,8):value=((value^((word>>shift)&255))*1099511628211)&mask
        return value
    outcomes={}
    for mode,result in proof['modes'].items():
        assert all(not row['immutable_admission'] and not row['edge_identity'] for row in manifest['modes'][mode]['runs'])
        prefix=base/f'{mode}_0';state=[list(r) for r in original]
        costs=[[r[2],r[3]] for r in original]
        for row in state:row[2]=row[3]=0
        owners=defaultdict(set);trees={net:{source:None} for net,source in sources.items()}
        paths={};q={task:min(t['criticality'],cfg['criticality_cap_q']) for task,t in tasks.items()}
        ordered={net:sorted(ids,key=lambda t:(tasks[t]['priority'],t)) for net,ids in net_tasks.items()}
        order=sorted(sources,key=lambda net:(tasks[ordered[net][0]]['priority'],ordered[net][0],net))
        trace=table(Path(str(prefix)+'.attachments.csv'))
        accepted={(r['iteration'],r['task_id']):r for r in trace};assert len(accepted)==len(trace)
        branches=defaultdict(list)
        for r in table(Path(str(prefix)+'.attachment_branches.csv')):branches[r['row']].append((r['index'],r['node']))
        pending=defaultdict(set)
        for r in table(Path(str(prefix)+'.pending_nets.csv')):pending[r['iteration']].add(r['net_id'])
        checkpoints={r['iteration']:r for r in table(Path(str(prefix)+'.audit.csv'))}
        assert all(row['issue_width']==cfg['issue_width'] for row in checkpoints.values())
        factors={r['iteration']:r['present_factor_q'] for r in table(Path(str(prefix)+'.iterations.csv'))}
        version_steps=dict(backend_commits=0,owner_refresh=0,global_cost=0)
        def increment(node,kind):
            assert state[node][4]<none;state[node][4]+=1;version_steps[kind]+=1
        def refresh(dirty):
            for node in dirty:
                base_state=original[node];known=set(owners[node])
                if base_state[0] and base_state[5]!=none:known.add(base_state[5])
                occupancy=base_state[0]+sum(not(base_state[0] and base_state[5]==net) for net in owners[node])
                owner=next(iter(known)) if occupancy==1 and len(known)==1 else none
                assert occupancy<=65535
                if (state[node][0],state[node][5])!=(occupancy,owner):
                    state[node][0]=occupancy;state[node][5]=owner;increment(node,'owner_refresh')
        def update_cost(present,history_step):
            for node,row in enumerate(state):
                new=[present,costs[node][1]+history_step*max(0,row[0]-row[1])]
                assert all(value<=mask for value in new)
                if new!=costs[node]:increment(node,'global_cost')
                costs[node]=new
        update_cost(256,0);next_trace=0;batches=0
        for iteration in range(result['iterations']):
            assert factors[iteration]==256*(2**iteration)
            if iteration:
                dirty=set()
                for net in order:
                    if net not in pending[iteration]:continue
                    for node,parent in trees[net].items():
                        if parent is not None:owners[node].remove(net);dirty.add(node)
                    trees[net]={sources[net]:None}
                    for task in net_tasks[net]:paths.pop(task,None)
                refresh(dirty)
            cursors={net:0 for net in pending[iteration]}
            while True:
                wave=[]
                for net in order:
                    if net not in cursors:continue
                    cursor=cursors[net]
                    if cursor<len(ordered[net]):wave.append(ordered[net][cursor]);cursors[net]+=1
                if not wave:break
                for start in range(0,len(wave),cfg['issue_width']):
                    batch=wave[start:start+cfg['issue_width']];batches+=1;dirty=set()
                    # Backend commits use priority order, not dispatch order.
                    for task in sorted(batch,key=lambda t:(tasks[t]['priority'],t)):
                        row=accepted.get((iteration,task))
                        if row is None:continue
                        for index,node in sorted(branches[row['row']]):
                            resource=state[node]
                            if resource[5]!=tasks[task]['net']:
                                assert resource[0]<65535
                                resource[5]=tasks[task]['net'] if resource[0]==0 else none
                                resource[0]+=1;increment(node,'backend_commits');dirty.add(node)
                    # Controller receives in dispatch order; refresh follows batch.
                    for task in batch:
                        row=accepted.get((iteration,task))
                        if row is None:continue
                        assert row['row']==next_trace;next_trace+=1
                        net=tasks[task]['net'];tree=trees[net];attachment=row['attachment']
                        chain=[];node=attachment
                        while node!=sources[net]:
                            assert node not in chain;chain.append(node);node=tree[node]
                        chain.reverse();parent=attachment
                        branch=[n for index,n in sorted(branches[row['row']])]
                        for node in branch:
                            assert node not in tree;tree[node]=parent;owners[node].add(net);dirty.add(node);parent=node
                        paths[task]=chain+branch
                    refresh(dirty)
            resource_hash=fnv_words(value for node,row in enumerate(state)
                for value in (row[0],row[1],costs[node][0],costs[node][1],row[4],row[5]))
            route_hash=fnv_words(value for task in tasks
                for value in (task,int(task in paths),len(paths.get(task,[])),*paths.get(task,[])))
            assert resource_hash==checkpoints[iteration]['resource_hash'],('resource',iteration)
            assert route_hash==checkpoints[iteration]['route_hash'],('route',iteration)
            feedback={r['task_id']:min(r['criticality_q'],cfg['criticality_cap_q']) for r in table(Path(str(prefix)+f'.timing_iteration_{iteration}.output.csv'))}
            q=feedback
            ordered={net:sorted(ids,key=lambda task:(-q[task],tasks[task]['priority'],task)) for net,ids in net_tasks.items()}
            order=sorted(sources,key=lambda net:(-q[ordered[net][0]],tasks[ordered[net][0]]['priority'],ordered[net][0],net))
            if iteration+1<result['iterations']:update_cost(factors[iteration+1],256)
        assert next_trace==len(trace)
        actual=binary(Path(str(prefix)+'.resources'),'<HHHHII')
        assert actual==[tuple(row) for row in state]
        actual_costs=binary(Path(str(prefix)+'.costs'),'<QQ');assert actual_costs==[tuple(row) for row in costs]
        outcomes[mode]=dict(epoch_hashes_matched=result['iterations'],batches=batches,
                            accepted_proposals=len(trace),version_increments=version_steps,
                            final_resources_and_costs_byte_equivalent=True)
    report=dict(status='serial_version_history_matches_epoch_and_final_checkpoints',modes=outcomes,
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                scope='VPR node-mode serial schedule with frozen default cost coefficients. Reconstructs priority-ordered backend commits, dispatch-ordered tree publication, ripups, owner refresh and cost-version updates. Matches each recorded epoch hash and final binary. Intermediate per-CU/read-version receipts and hardware atomicity are not independently observed.',
                board_result=False,research_complete=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],modes=outcomes)))
