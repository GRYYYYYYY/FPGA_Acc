"""Reconstruct serial commits/owner refresh/cost epochs and compare checkpoints."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import struct
from rr_resource_version_replay import ResourceVersions,replay_private_versions
import rr_resource_version_replay

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('pending_audit',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    pair=a.manifest.resolve();base=pair.parent;proof_path=a.pending_audit.resolve()
    proof=json.loads(proof_path.read_text())
    assert proof['status']=='five_repeat_net_trial_paths_pending_and_predicates_audited'
    assert all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==h for path,h in proof['source_sha256'].items())
    assert proof['source_sha256'][str(pair)]==hashlib.sha256(pair.read_bytes()).hexdigest()
    manifest=json.loads(pair.read_text());cfg=manifest['configuration']
    assert not cfg['speculative_workers'] and not cfg['cleanup_passes'] and cfg['task_order']=='preserve'
    assert cfg['cost_state_bits']==64 and cfg['timing_updates']
    transaction_mode=cfg['supplemental_transaction_mode'];assert transaction_mode in (0,1,2)
    header=(base/'source/persistroute/include/pathfinder.hpp').read_text()
    for text in ('present_start_q = 256','present_multiplier_q = 512','history_increment_q = 256'):
        assert text in header,'This replay covers the frozen default cost schedule only'
    files=[Path(__file__),Path(rr_resource_version_replay.__file__),pair,proof_path,base/'source/persistroute/include/pathfinder.hpp']
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
        prefix=base/f'{mode}_0';model=ResourceVersions(original)
        state,costs,owners=model.state,model.costs,model.owners
        trees={net:{source:None} for net,source in sources.items()}
        paths={};q={task:min(t['criticality'],cfg['criticality_cap_q']) for task,t in tasks.items()}
        ordered={net:sorted(ids,key=lambda t:(tasks[t]['priority'],t)) for net,ids in net_tasks.items()}
        order=sorted(sources,key=lambda net:(tasks[ordered[net][0]]['priority'],ordered[net][0],net))
        trace=table(Path(str(prefix)+'.attachments.csv'))
        accepted={(r['iteration'],r['task_id']):r for r in trace};assert len(accepted)==len(trace)
        branches=defaultdict(list)
        for r in table(Path(str(prefix)+'.attachment_branches.csv')):branches[r['row']].append((r['index'],r['node']))
        pending=defaultdict(set)
        pending_reasons=defaultdict(dict)
        for r in table(Path(str(prefix)+'.pending_nets.csv')):
            pending[r['iteration']].add(r['net_id']);pending_reasons[r['iteration']][r['net_id']]=r['reasons']
        trial_tables={name:table(Path(str(prefix)+'.'+name+'.csv')) for name in ('net_trials','net_trial_steps','net_trial_branches')}
        trials_by_iteration=defaultdict(list)
        for r in trial_tables['net_trials']:trials_by_iteration[r['iteration']].append(r)
        assert len(trial_tables['net_trials'])==result['net_trials']
        checkpoints={r['iteration']:r for r in table(Path(str(prefix)+'.audit.csv'))}
        assert all(row['issue_width']==cfg['issue_width'] for row in checkpoints.values())
        factors={r['iteration']:r['present_factor_q'] for r in table(Path(str(prefix)+'.iterations.csv'))}
        attempted_private=dict(backend_commits=0,owner_refresh=0,global_cost=0)
        discarded_private=dict(attempted_private)
        model.update_cost(256,0);costs=model.costs
        next_trace=0;batches=0;private_queries=private_hashes=published_trials=discarded_trials=0
        for iteration in range(result['iterations']):
            assert factors[iteration]==256*(2**iteration)
            staged={net for net in pending[iteration] if transaction_mode and pending_reasons[iteration][net]==8}
            ordinary_pending=pending[iteration]-staged
            if iteration:
                dirty=set()
                for net in order:
                    if net not in ordinary_pending:continue
                    for node,parent in trees[net].items():
                        if parent is not None:owners[node].remove(net);dirty.add(node)
                    trees[net]={sources[net]:None}
                    for task in net_tasks[net]:paths.pop(task,None)
                model.refresh(dirty)
            cursors={net:0 for net in ordinary_pending}
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
                        branch=[node for index,node in sorted(branches[row['row']])]
                        model.backend_commit(branch,tasks[task]['net']);dirty.update(branch)
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
                    model.refresh(dirty)
            for trial in trials_by_iteration[iteration]:
                assert trial['mode']==transaction_mode and trial['net_id'] in staged
                model,trees,paths,attempted=replay_private_versions(model,trial,trial_tables,trees,paths,
                    sources[trial['net_id']],set(net_tasks[trial['net_id']]),list(tasks))
                state,costs,owners=model.state,model.costs,model.owners
                for kind,value in attempted.items():
                    attempted_private[kind]+=value
                    if not trial['accepted']:discarded_private[kind]+=value
                private_queries+=trial['steps'];private_hashes+=4+2*trial['steps']
                published_trials+=int(bool(trial['accepted']));discarded_trials+=int(not trial['accepted'])
            resource_hash=model.resource_hash()
            route_hash=fnv_words(value for task in tasks
                for value in (task,int(task in paths),len(paths.get(task,[])),*paths.get(task,[])))
            assert resource_hash==checkpoints[iteration]['resource_hash'],('resource',iteration)
            assert route_hash==checkpoints[iteration]['route_hash'],('route',iteration)
            feedback={r['task_id']:min(r['criticality_q'],cfg['criticality_cap_q']) for r in table(Path(str(prefix)+f'.timing_iteration_{iteration}.output.csv'))}
            q=feedback
            ordered={net:sorted(ids,key=lambda task:(-q[task],tasks[task]['priority'],task)) for net,ids in net_tasks.items()}
            order=sorted(sources,key=lambda net:(-q[ordered[net][0]],tasks[ordered[net][0]]['priority'],ordered[net][0],net))
            if iteration+1<result['iterations']:
                model.update_cost(factors[iteration+1],256);costs=model.costs
        assert next_trace==len(trace)
        actual=binary(Path(str(prefix)+'.resources'),'<HHHHII')
        assert actual==[tuple(row) for row in state]
        actual_costs=binary(Path(str(prefix)+'.costs'),'<QQ');assert actual_costs==[tuple(row) for row in costs]
        assert set(trials_by_iteration)<=set(range(result['iterations']))
        outcomes[mode]=dict(epoch_hashes_matched=result['iterations'],ordinary_batches=batches,
                            private_queries=private_queries,private_resource_hash_fields_matched=private_hashes,
                            ordinary_accepted_proposals=len(trace),published_net_trials=published_trials,
                            rejected_net_trials=discarded_trials,authoritative_version_increments=model.increments,
                            all_private_attempt_version_increments=attempted_private,
                            discarded_private_version_increments=discarded_private,
                            final_resources_and_costs_byte_equivalent=True)
    report=dict(status='private_and_published_versions_match_trial_epoch_and_final_checkpoints',modes=outcomes,
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                scope='Frozen default VPR node-mode serial CPU cost schedule. Ordinary dispatch/commit and private ripup/backend/owner transitions reconstructed from initially exported authority; private before/intermediate/final/publication hashes, all epoch hashes and final resource/cost binaries matched. Rejected private version increments remain separate from authoritative history. Requires passed full path/predicate audit. No independent search-work oracle, per-CU read-version receipts, physical execution or asynchronous hardware atomicity proof.',
                board_result=False,research_complete=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],modes=outcomes)))
