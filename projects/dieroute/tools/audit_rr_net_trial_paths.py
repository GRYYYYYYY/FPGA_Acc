"""Independently reconstruct feedback decisions, pending nets and CPU authority."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import struct
from audit_rr_experiments import audit
from rr_net_trial_replay import replay_trial
import rr_net_trial_replay

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    manifest_path=a.manifest.resolve();base=manifest_path.parent
    verified=audit(manifest_path);manifest=json.loads(manifest_path.read_text());cfg=manifest['configuration']
    transaction_mode=cfg["supplemental_transaction_mode"];assert transaction_mode in (0,1,2)
    assert cfg["task_order"]=="preserve"
    threshold=cfg['criticality_feedback_threshold_q'];assert threshold in (0,64880)
    guard=cfg["feedback_local_delay_guard"];assert isinstance(guard,bool) and (not guard or threshold)
    assert cfg['cost_state_bits']==64 and not cfg['cleanup_passes'] and not cfg['speculative_workers']
    assert cfg['timing_updates']
    files=[manifest_path,Path(__file__),Path(rr_net_trial_replay.__file__)]
    def table(path):
        files.append(path)
        with path.open() as stream:return [{k:int(v) for k,v in row.items()} for row in csv.DictReader(stream)]
    def binary(path,layout):files.append(path);return list(struct.iter_unpack(layout,path.read_bytes()))
    nodes=binary(base/'input.nodes','<IHH');edges=binary(base/'input.edges','<IHH')
    initial=binary(base/'input.resources','<HHHHII')
    connection_file=Path(manifest['reference'])/'connections.csv';files.append(connection_file)
    with connection_file.open() as stream:
        tasks={int(r['id']):{k:int(r[k]) for k in ('net_id','source','sink','criticality_q','max_hops')} for r in csv.DictReader(stream)}
    input_tasks=binary(base/'input.tasks','<IIIIHHIII')
    input_order=[r[0] for r in input_tasks]
    assert set(input_order)==set(tasks) and len(input_order)==len(tasks)
    for r in input_tasks:
        tasks[r[0]].update(priority=r[6],epoch=r[7],reserved=r[8])
    def route_hash(paths):
        value=1469598103934665603
        for task in input_order:
            path=paths.get(task,[])
            for word in [task,int(task in paths),len(path),*path]:
                for byte in word.to_bytes(8,'little'):value=((value^byte)*1099511628211)&((1<<64)-1)
        return value
    sources={};net_tasks=defaultdict(set)
    for task,t in tasks.items():
        assert t['source']!=t['sink'];net_tasks[t['net_id']].add(task)
        assert sources.setdefault(t['net_id'],t['source'])==t['source']
    def delay(parent,child,minimum=False):
        begin,count,_=nodes[parent];assert begin+count<=len(edges)
        values=[d for dst,c,d in edges[begin:begin+count] if dst==child];assert values
        return min(values) if minimum else values[0]
    outcomes={}
    for mode,proof in verified['modes'].items():
        assert proof['repeats_verified']==5 and not proof['counters']['edge_identity']
        for i in range(5):
            step,=[s for s in manifest['steps'] if s['label']==f'{mode}_{i}']
            env=step['routing_environment'];assert env['DIEROUTE_CRITICAL_FEEDBACK_THRESHOLD_Q']==str(threshold)
            assert env['DIEROUTE_TIMING_UPDATE_PERIOD']=='1'
            assert env['DIEROUTE_SUPPLEMENTAL_TRANSACTION_MODE']==str(transaction_mode)
            assert manifest['modes'][mode]['runs'][i]['supplemental_transaction_mode']==transaction_mode
            assert env['DIEROUTE_FEEDBACK_LOCAL_DELAY_GUARD']==str(int(guard))
            assert manifest['modes'][mode]['runs'][i]['feedback_local_delay_guard']==int(guard)
            assert manifest['modes'][mode]['runs'][i]['criticality_feedback_threshold_q']==threshold
        prefix=base/f'{mode}_0'
        trial_tables={name:table(Path(str(prefix)+'.'+name+'.csv')) for name in
                      ('net_trials','net_trial_steps','net_trial_seeds','net_trial_branches','net_trial_connections','net_trial_paths')}
        trial_rows=trial_tables['net_trials'];assert [r['trial'] for r in trial_rows]==list(range(len(trial_rows)))
        assert len(trial_rows)==proof['counters']['net_trial_count']
        assert transaction_mode or not trial_rows
        known_trials={r['trial'] for r in trial_rows}
        for name,rows in trial_tables.items():assert all(r['trial'] in known_trials for r in rows)
        trials_by_iteration=defaultdict(list)
        for r in trial_rows:trials_by_iteration[r['iteration']].append(r)
        epoch_audits={r['iteration']:r for r in table(Path(str(prefix)+'.audit.csv'))}
        epochs={task:t['epoch'] for task,t in tasks.items()}
        private_expanded=private_edge_visits=private_steps=accepted_trials=0
        grouped=defaultdict(list);pending_log=defaultdict(dict);feedback_log=defaultdict(list)
        for i,row in enumerate(table(Path(str(prefix)+'.attachments.csv'))):
            assert row['row']==i;grouped[row['iteration']].append(row)
        branches=defaultdict(list)
        for row in table(Path(str(prefix)+'.attachment_branches.csv')):branches[row['row']].append((row['index'],row['node']))
        for row in table(Path(str(prefix)+'.pending_nets.csv')):
            group=pending_log[row['iteration']];assert row['net_id'] not in group;group[row['net_id']]=row['reasons']
        feedback_rows=table(Path(str(prefix)+'.critical_feedback.csv'))
        for row in feedback_rows:feedback_log[row['iteration']].append(row)
        assert len(feedback_rows)==proof['counters']['critical_feedback_events']
        iteration_log={r['iteration']:r for r in table(Path(str(prefix)+'.iterations.csv'))}
        trees={net:{source:None} for net,source in sources.items()};routed=set();paths={}
        pending={net:16 for net in sources};used=set();events=0
        previous_inputs=None
        previous_criticality={task:min(t['criticality_q'],cfg['criticality_cap_q']) for task,t in tasks.items()}
        total=proof['counters']['iterations']
        assert set(pending_log)==set(range(total))
        assert set(grouped)<=set(range(total)) and set(feedback_log)<=set(range(total))
        for iteration in range(total):
            assert pending_log[iteration]==pending
            staged={net for net,reason in pending.items() if transaction_mode and reason==8}
            ordinary_pending=set(pending)-staged
            for net in ordinary_pending:
                for task in net_tasks[net]:epochs[task]=iteration
                trees[net]={sources[net]:None};routed-=net_tasks[net]
                for task in net_tasks[net]:paths.pop(task,None)
            seen=set()
            for row in grouped[iteration]:
                task=row['task_id'];t=tasks[task];net=t['net_id'];tree=trees[net]
                assert net in ordinary_pending and task not in seen;seen.add(task)
                assert row['criticality_q']==previous_criticality[task]
                assert (row['net_id'],row['source'],row['sink'])==(net,t['source'],t['sink'])
                attachment=row['attachment'];assert attachment in tree and len(tree)==row['tree_nodes_before']
                chain=[];node=attachment
                while node!=t['source']:
                    assert node not in chain and tree[node] is not None;chain.append(node);node=tree[node]
                chain.reverse();parent=t['source'];cost=0
                for node in chain:cost+=delay(parent,node);parent=node
                assert cost==row['prefix_delay_q'] and len(chain)==row['seed_hops']
                scale=cfg['cost_scale'];weight=cfg['route_tree_timing_weight_q'];q=row['criticality_q']
                charge=(cost*q//65535)*weight//256 if scale==1 else cost*q*scale*weight//(65535*256)
                assert charge==row['seed_cost_q']
                branch=sorted(branches.pop(row['row'],[]));assert [i for i,n in branch]==list(range(row['branch_nodes']))
                branch=[n for i,n in branch];assert (branch[-1] if branch else attachment)==t['sink']
                assert len(chain)+len(branch)<=t['max_hops'];parent=attachment;cost=0
                for node in branch:assert node not in tree;cost+=delay(parent,node);tree[node]=parent;parent=node
                assert cost==row['branch_delay_q'];paths[task]=chain+branch;routed.add(task)
            ordered=lambda net:sorted(net_tasks[net],key=lambda task:(-previous_criticality[task],tasks[task]['priority'],task))
            ordered_staged=sorted(staged,key=lambda net:(-previous_criticality[ordered(net)[0]],tasks[ordered(net)[0]]['priority'],ordered(net)[0],net))
            actual_trials=trials_by_iteration[iteration]
            assert [r['net_id'] for r in actual_trials]==ordered_staged,'Incorrect staged net order'
            iteration_failed_trials=iteration_published=iteration_steps=0
            for trial in actual_trials:
                assert trial['mode']==transaction_mode
                assert trial['before_route_hash']==route_hash(paths),'Incorrect pretrial authoritative paths'
                for r in trial_tables['net_trial_connections']:
                    if r['trial']==trial['trial'] and r['stage']==0:assert r['epoch']==epochs[r['task_id']]
                replay=replay_trial(trial,trial_tables,nodes,edges,initial,trees,paths,tasks,previous_criticality,
                                    cfg['cost_scale'],cfg['route_tree_timing_weight_q'])
                trees,paths=replay['trees'],replay['paths'];routed=set(paths)
                assert trial['after_route_hash']==route_hash(paths),'Incorrect trial publication paths'
                if replay['accepted']:
                    accepted_trials+=1;iteration_published+=len(net_tasks[trial['net_id']])
                    for task in net_tasks[trial['net_id']]:epochs[task]=iteration
                iteration_failed_trials+=int(not trial['complete'])
                iteration_steps+=trial['steps'];private_steps+=trial['steps']
                private_expanded+=replay['expanded'];private_edge_visits+=replay['edge_visits']
            ordinary_failed=sum(len(net_tasks[net]) for net in ordinary_pending)-len(seen)
            epoch=epoch_audits[iteration]
            assert epoch['committed']==len(seen)+iteration_published
            assert epoch['failed']==ordinary_failed+iteration_failed_trials
            assert epoch['route_hash']==route_hash(paths),'Epoch authoritative route hash differs'
            inputs={r['task_id']:r for r in table(Path(str(prefix)+f'.timing_iteration_{iteration}.input.csv'))}
            outputs={r['task_id']:r for r in table(Path(str(prefix)+f'.timing_iteration_{iteration}.output.csv'))}
            assert inputs.keys()==outputs.keys()==tasks.keys()
            for task,t in tasks.items():
                assert inputs[task]['criticality_q']==previous_criticality[task]
                assert inputs[task]['routed']==int(task in routed)
                parent=t['source'];cost=0
                for node in paths.get(task,[]):cost+=delay(parent,node,True);parent=node
                assert inputs[task]['delay_ps']==cost
            current={t:min(r['criticality_q'],cfg['criticality_cap_q']) for t,r in outputs.items()}
            owners=defaultdict(set)
            for net,tree in trees.items():
                for node,parent in tree.items():
                    if parent is not None:owners[node].add(net)
            occupancy=[r[0]+sum(not(r[0] and r[5]==net) for net in owners[node]) for node,r in enumerate(initial)]
            over=[node for node,r in enumerate(initial) if occupancy[node]>r[1]]
            ordinary={};force=iteration+1<cfg['min_timing_iterations']
            if force:ordinary={net:1 for net in sources}
            for task,t in tasks.items():
                if task not in routed:ordinary[t['net_id']]=ordinary.get(t['net_id'],0)|2
            for node in over:
                for net in owners[node]:ordinary[net]=ordinary.get(net,0)|4
            crossings={}
            if threshold:
                for task in sorted(tasks):
                    net=tasks[task]['net_id']
                    eligible=(not guard or (previous_inputs is not None and
                        previous_inputs[task]['routed']==inputs[task]['routed']==1 and
                        inputs[task]['delay_ps']>previous_inputs[task]['delay_ps']))
                    if previous_criticality[task]<threshold<=current[task] and eligible:crossings.setdefault(net,task)
            expected=[];supplemental=False
            for net,task in sorted(crossings.items()):
                decision=0 if net in ordinary else 2 if net in used else 3 if iteration+1>=cfg['max_iterations'] else 1
                if decision==1:ordinary[net]=8;used.add(net);supplemental=True;events+=1
                expected.append(dict(iteration=iteration,net_id=net,task_id=task,old_q=previous_criticality[task],new_q=current[task],decision=decision))
            assert feedback_log[iteration]==expected
            log=iteration_log[iteration]
            assert log['routed_nets']==len(pending) and log['overused_resources']==len(over)
            assert log['failed_connections']==ordinary_failed
            legal=len(routed)==len(tasks) and not over
            if legal and not force and not supplemental:assert iteration==total-1
            if iteration==total-1:assert legal or total==cfg['max_iterations']
            previous_inputs=inputs
            previous_criticality=current;pending=ordinary
        assert not branches
        assert set(trials_by_iteration)<=set(range(total))
        assert private_expanded<=proof['counters']['expanded'] and private_edge_visits<=proof['counters']['edge_visits']
        final=binary(Path(str(prefix)+'.resources'),'<HHHHII')
        assert len(final)==len(initial)
        for node,(old,actual) in enumerate(zip(initial,final)):
            known=set(owners[node])
            if old[0] and old[5]!=0xffffffff:known.add(old[5])
            owner=next(iter(known)) if occupancy[node]==1 and len(known)==1 else 0xffffffff
            assert actual[0]==occupancy[node] and actual[5]==owner
        final_paths=defaultdict(list)
        for row in table(Path(str(prefix)+'.paths.csv')):final_paths[row['task_id']].append((row['path_index'],row['resource_id']))
        assert set(final_paths)==set(paths)
        for task,path_nodes in paths.items():
            values=sorted(final_paths[task]);assert [i for i,node in values]==list(range(len(values)))
            assert [node for i,node in values]==path_nodes
        final_trees=table(Path(str(prefix)+'.route_trees.csv'))
        assert {(r['net_id'],r['child']):r['parent'] for r in final_trees}=={(net,node):parent for net,tree in trees.items() for node,parent in tree.items() if parent is not None}
        assert bool(proof['counters']['legal'])==bool(legal)
        outcomes[mode]=dict(iterations=total,supplemental_nets=len(used),supplemental_events=events,
                            feedback_events=len(feedback_rows),cpu_legal=bool(legal),local_delay_guard=guard,
                            transaction_mode=transaction_mode,net_trials=len(trial_rows),accepted_trials=accepted_trials,
                            private_steps=private_steps,private_expanded=private_expanded,private_edge_visits=private_edge_visits)
    report=dict(status='five_repeat_net_trial_paths_pending_and_predicates_audited',modes=outcomes,
                source_sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                scope='Five-repeat root native/determinism audit plus ordinary/staged ordering, complete private seeds/paths/delay/wire/capacity predicates, publication path hashes, feedback/pending and final occupancy/owner replay. Private reported work is bounded by global counters, not independently re-executed. Private/intermediate/published resource-version hash reconstruction remains a separate required audit. No policy acceptance or hardware atomicity claim.',
                research_complete=False,board_result=False)
    assert not a.output.exists();a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],modes=outcomes)))
