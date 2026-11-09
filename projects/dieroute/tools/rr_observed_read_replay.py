"""Replay observed resource values,shadow versions and stale classifications alongside seeds and authority."""
from collections import defaultdict
import csv
import hashlib
from pathlib import Path
import struct
import itertools
from rr_resource_version_replay import ResourceVersions, route_hash
import rr_resource_version_replay


def replay(input_prefix, output_prefix, schedule_mode, issue_width, min_timing_iterations,
           cost_scale=1, timing_weight=128, criticality_cap=64880, topology_prefix=None, workers=2, shadow_sync=1):
    assert schedule_mode in (0, 1, 2) and issue_width > 0
    source_files = [Path(__file__).resolve(), Path(rr_resource_version_replay.__file__).resolve()]

    def binary(path, layout):
        source_files.append(path)
        return list(struct.iter_unpack(layout, path.read_bytes()))

    def table(suffix):
        path = Path(str(output_prefix) + '.' + suffix)
        source_files.append(path)
        with path.open() as stream:
            return [{k: int(v) for k, v in r.items()} for r in csv.DictReader(stream)]

    nodes = binary(Path(str(input_prefix) + '.nodes'), '<IHH')
    edges = binary(Path(str(input_prefix) + '.edges'), '<IHH')
    original = binary(Path(str(input_prefix) + '.resources'), '<HHHHII')
    raw_tasks = binary(Path(str(input_prefix) + '.tasks'), '<IIIIHHIII')
    ids = [r[0] for r in raw_tasks]
    tasks = {r[0]: dict(net=r[1], source=r[2], sink=r[3], q=r[4], hops=r[5], priority=r[6]) for r in raw_tasks}
    assert len(ids) == len(tasks) and len(original) == len(nodes)
    assert all(begin + count <= len(edges) for begin, count, span in nodes)
    net_tasks, roots = defaultdict(list), {}
    for task, t in tasks.items():
        net_tasks[t['net']].append(task)
        assert roots.setdefault(t['net'], t['source']) == t['source']
    q = {task: min(t['q'], criticality_cap) for task, t in tasks.items()}
    ordered = {net: sorted(ts, key=lambda task: (tasks[task]['priority'], task)) for net, ts in net_tasks.items()}
    order = sorted(roots, key=lambda net: (tasks[ordered[net][0]]['priority'], ordered[net][0], net))
    trees, paths = {net: {root: None} for net, root in roots.items()}, {}
    model = ResourceVersions(original)
    model.update_cost(256, 0)
    trace = table('attachments.csv')
    assert [r['row'] for r in trace] == list(range(len(trace)))
    accepted = {(r['iteration'], r['task_id']): r for r in trace}
    assert len(accepted) == len(trace)
    branches = defaultdict(list)
    for row in table('attachment_branches.csv'):
        branches[row['row']].append((row['index'], row['node']))
    ripups = table('ordinary_ripups.csv')
    iterations = table('iterations.csv')
    audits = table('audit.csv')
    assert iterations
    assert [r['iteration'] for r in iterations] == [r['iteration'] for r in audits] == list(range(len(iterations)))
    pending_trace = defaultdict(dict)
    for row in table('pending_nets.csv'):
        group = pending_trace[row['iteration']]
        assert row['net_id'] not in group
        group[row['net_id']] = row['reasons']
    assert not table('critical_feedback.csv') and not table('net_trials.csv')
    pending = {net: 16 for net in roots}
    next_ripup = next_attachment = batches = failures = 0
    migration = {}
    for row in table('task_migration.csv'):
        key = (row['epoch'], row['task_id'])
        assert key not in migration and row['executed'] == 1
        migration[key] = row
    received = defaultdict(list)
    seed_rows = table('received_task_seeds.csv')
    for row in seed_rows:
        key = (row['epoch'], row['task_id'])
        assert key in migration and row['window'] == migration[key]['window']
        received[key].append((row['seed_index'], row['node'], row['hops'], row['cost_q']))
    assert set(received) == set(migration)
    checked_requests = set()
    assert topology_prefix is not None and workers>0 and shadow_sync>0
    owners = [r[0] for r in binary(Path(str(topology_prefix)+'.node_die'), '<H')]
    membership_path=Path(str(topology_prefix)+'.node_membership')
    boundary=set()
    if membership_path.exists():
        members=[r[0] for r in binary(membership_path,'<H')]
        boundary={i for i,v in enumerate(members) if v & (v-1)}
    else:
        for node,(begin,count,span) in enumerate(nodes):
            for dst,cost,d in edges[begin:begin+count]:
                if owners[node]!=owners[dst]:boundary.update([node,dst])
    transaction_path=Path(str(output_prefix)+'.transactions.csv');source_files.append(transaction_path)
    with transaction_path.open() as stream:transaction_rows=list(csv.DictReader(stream))
    transactions={}
    for row in transaction_rows:
        key=(int(row['epoch']),int(row['task_id']))
        assert key not in transactions
        transactions[key]=row
    read_path=Path(str(output_prefix)+'.observed_reads.bin');source_files.append(read_path)
    record=struct.Struct('<QIIIIIIHHHHIIQQ');assert record.size==64
    def records():
        with read_path.open('rb') as stream:
            while True:
                block=stream.read(record.size)
                if not block:return
                assert len(block)==record.size,'truncated read record'
                yield record.unpack(block)
    groups=itertools.groupby(records(),key=lambda row:row[:5])
    pending_group=next(groups,None)
    published={};next_window=0;checked_transactions=set()
    observed_rows=remote_rows=stale_proposals=fresh_replays=0
    def read_group(key,count,hash_value,base,base_cost,live,observer,initial):
        nonlocal pending_group,observed_rows,remote_rows
        if not count:
            assert hash_value==1469598103934665603
            return False
        assert pending_group is not None and pending_group[0]==key,('read group identity',key)
        unique=set();words=[];stale=False;observed=0
        for row in pending_group[1]:
            window,task,epoch,phase,die,index,node,occ,cap,p16,h16,version,owner,present,history=row
            assert index==observed and node<len(base) and node not in unique
            unique.add(node);observed+=1
            expected=list(base[node]);cost=base_cost[node]
            if initial and node in boundary and owners[node]!=observer:
                old_occ,old_cap,old_version,old_present,old_history=published[node]
                expected[0],expected[1],expected[4]=old_occ,old_cap,old_version
                cost=(old_present,old_history);remote_rows+=1
            assert (occ,cap,p16,h16,version,owner)==tuple(expected),('read resource mismatch',key,index,node)
            assert (present,history)==tuple(cost),('read wide cost mismatch',key,index,node)
            words.extend((node,version));stale|=version!=live[node][4]
        from rr_resource_version_replay import fnv_words
        assert observed==count and fnv_words(words)==hash_value,'read count/hash mismatch'
        observed_rows+=observed;pending_group=next(groups,None)
        return stale



    def prefix(tree, node):
        chain = []
        while tree[node] is not None:
            assert node not in chain
            chain.append(node)
            node = tree[node]
        return list(reversed(chain))

    def delay(source, path, minimum):
        total = 0
        for node in path:
            begin, count, span = nodes[source]
            values = [d for dst, cost, d in edges[begin:begin + count] if dst == node]
            assert values
            total += min(values) if minimum else values[0]
            source = node
        return total

    for iteration, (iteration_row, audit) in enumerate(zip(iterations, audits)):
        assert pending_trace[iteration] == pending
        assert iteration_row['present_factor_q'] == 256 * 2**iteration
        expected_width = 1 if schedule_mode == 2 else issue_width
        assert audit['issue_width'] == expected_width
        batch_index, seen, started = 0, set(), set()

        def ripup(net):
            nonlocal next_ripup
            tree = trees[net]
            expected = dict(iteration=iteration, net_id=net, dispatch_batch=batch_index,
                            phase=schedule_mode, tree_nodes_before=len(tree),
                            routed_connections_before=sum(task in paths for task in net_tasks[net]))
            assert next_ripup < len(ripups) and ripups[next_ripup] == expected, 'Incorrect ripup dispatch or incumbent'
            next_ripup += 1
            dirty = {node for node, parent in tree.items() if parent is not None}
            for node in dirty:
                model.owners[node].remove(net)
            trees[net] = {roots[net]: None}
            for task in net_tasks[net]:
                paths.pop(task, None)
            return dirty

        if iteration and schedule_mode == 0:
            dirty = set()
            for net in order:
                if net in pending:
                    dirty.update(ripup(net))
            model.refresh(dirty)
        cursors = {net: 0 for net in pending}
        while True:
            wave = []
            for net in order:
                if net in cursors and cursors[net] < len(ordered[net]):
                    wave.append(ordered[net][cursors[net]])
                    cursors[net] += 1
                    if schedule_mode == 2:
                        break
            if not wave:
                break
            for start in range(0, len(wave), expected_width):
                batch = wave[start:start + expected_width]
                if schedule_mode:
                    dirty = set()
                    for task in batch:
                        net = tasks[task]['net']
                        if net not in started:
                            started.add(net)
                            if iteration:
                                dirty.update(ripup(net))
                    model.refresh(dirty)
                if migration:
                    for task in batch:
                        key = (iteration, task)
                        assert key in received and key not in checked_requests
                        checked_requests.add(key)
                        t = tasks[task]
                        expected = []
                        for index, node in enumerate(sorted(trees[t['net']])):
                            chain = prefix(trees[t['net']], node)
                            arrival = delay(t['source'], chain, False)
                            charge = ((arrival * q[task] // 65535) * timing_weight // 256 if cost_scale == 1 else
                                      arrival * q[task] * cost_scale * timing_weight // (65535 * 256))
                            assert charge <= 0xffffffff
                            expected.append((index, node, len(chain), charge))
                        assert received[key] == expected, ('complete receiver seed mismatch', key)
                        assert len(expected) == migration[key]['seed_count']
                proposals = {}
                for task in batch:
                    row = accepted.get((iteration, task))
                    if row is None:
                        continue
                    t, net = tasks[task], tasks[task]['net']
                    tree = trees[net]
                    assert (row['net_id'], row['source'], row['sink'], row['criticality_q']) == (net, t['source'], t['sink'], q[task])
                    assert row['tree_nodes_before'] == len(tree)
                    chain = prefix(tree, row['attachment'])
                    arrival = delay(t['source'], chain, False)
                    charge = ((arrival * q[task] // 65535) * timing_weight // 256 if cost_scale == 1 else
                              arrival * q[task] * cost_scale * timing_weight // (65535 * 256))
                    assert (row['seed_hops'], row['prefix_delay_q'], row['seed_cost_q']) == (len(chain), arrival, charge)
                    rows = sorted(branches[row['row']])
                    assert [index for index, node in rows] == list(range(row['branch_nodes']))
                    branch = [node for index, node in rows]
                    assert (branch[-1] if branch else row['attachment']) == t['sink']
                    assert len(chain) + len(branch) <= t['hops']
                    assert delay(row['attachment'], branch, False) == row['branch_delay_q']
                    assert len(set(branch)) == len(branch) and not set(branch).intersection(tree)
                    proposals[task] = (row, chain, branch)
                for slot,task in enumerate(sorted(batch,key=lambda task:(tasks[task]['priority'],task))):
                    if slot % workers == 0:
                        window=next_window;next_window+=1
                        window_base=[tuple(r) for r in model.state]
                        window_cost=[tuple(r) for r in model.costs]
                        if window % shadow_sync==0:
                            published={n:(window_base[n][0],window_base[n][1],window_base[n][4],window_cost[n][0],window_cost[n][1]) for n in boundary}
                    key=(iteration,task);tr=transactions[key]
                    assert key not in checked_transactions
                    checked_transactions.add(key)
                    assert int(tr['window'])==window
                    observer=migration[key]['execution_die'] if migration else owners[tasks[task]['source']]
                    identity=(window,task,iteration,0,observer)
                    stale=read_group(identity,int(tr['initial_reads']),int(tr['initial_read_hash']),window_base,window_cost,model.state,observer,True)
                    assert stale==(tr['initial_status']=='stale') and stale==bool(int(tr['replayed']))
                    if stale:
                        stale_proposals+=1;fresh_replays+=1
                        observer=owners[tasks[task]['source']]
                        again=read_group((window,task,iteration,1,observer),int(tr['final_reads']),int(tr['replay_read_hash']),model.state,model.costs,model.state,observer,False)
                        assert not again
                    else:
                        assert tr['initial_reads']==tr['final_reads'] and int(tr['replay_read_hash'])==0
                    assert (tr['final_status']=='committed')==(task in proposals)
                    if task in proposals:model.backend_commit(proposals[task][2],tasks[task]['net'])
                dirty = set()
                for task in batch:
                    if task not in proposals:
                        continue
                    row, chain, branch = proposals[task]
                    assert row['row'] == next_attachment
                    next_attachment += 1
                    seen.add(task)
                    net, parent = tasks[task]['net'], row['attachment']
                    for node in branch:
                        trees[net][node] = parent
                        model.owners[node].add(net)
                        dirty.add(node)
                        parent = node
                    paths[task] = chain + branch
                model.refresh(dirty)
                batch_index += 1
                batches += 1
        over = [node for node, row in enumerate(model.state) if row[0] > row[1]]
        failed = sum(len(net_tasks[net]) for net in pending) - len(seen)
        failures += failed
        assert audit['committed'] == len(seen) and audit['failed'] == failed
        assert iteration_row['failed_connections'] == failed and iteration_row['routed_nets'] == len(pending)
        assert iteration_row['overused_resources'] == len(over)
        assert audit['resource_hash'] == model.resource_hash(), ('resource', iteration)
        assert audit['route_hash'] == route_hash(paths, ids), ('route', iteration)
        inputs = table(f'timing_iteration_{iteration}.input.csv')
        outputs = table(f'timing_iteration_{iteration}.output.csv')
        assert len(inputs)==len(outputs)==len(tasks)
        assert {r['task_id'] for r in inputs} == {r['task_id'] for r in outputs} == set(tasks)
        for row in inputs:
            task = row['task_id']
            assert row['criticality_q'] == q[task] and row['routed'] == int(task in paths)
            assert row['delay_ps'] == delay(tasks[task]['source'], paths.get(task, []), True)
        q = {r['task_id']: min(r['criticality_q'], criticality_cap) for r in outputs}
        ordered = {net: sorted(ts, key=lambda task: (-q[task], tasks[task]['priority'], task)) for net, ts in net_tasks.items()}
        order = sorted(roots, key=lambda net: (-q[ordered[net][0]], tasks[ordered[net][0]]['priority'], ordered[net][0], net))
        force = iteration + 1 < min_timing_iterations
        legal = len(paths) == len(tasks) and not over
        if legal and not force:
            assert iteration == len(iterations) - 1
        pending = {net: 1 for net in roots} if force else {}
        for task, t in tasks.items():
            if task not in paths:
                pending[t['net']] = pending.get(t['net'], 0) | 2
        for node in over:
            for net in model.owners[node]:
                pending[net] = pending.get(net, 0) | 4
        if iteration + 1 < len(iterations):
            model.update_cost(256 * 2**(iteration + 1), 256)
    assert set(pending_trace)<=set(range(len(iterations)))
    assert next_ripup == len(ripups) and next_attachment == len(trace)
    assert set(branches) <= {r['row'] for r in trace}
    final = binary(Path(str(output_prefix) + '.resources'), '<HHHHII')
    final_costs = binary(Path(str(output_prefix) + '.costs'), '<QQ')
    assert final == [tuple(r) for r in model.state] and final_costs == [tuple(r) for r in model.costs]
    final_paths = defaultdict(list)
    for row in table('paths.csv'):
        final_paths[row['task_id']].append((row['path_index'], row['resource_id']))
    assert set(final_paths) == set(paths)
    for task, path in paths.items():
        assert sorted(final_paths[task]) == list(enumerate(path))
    final_trees = table('route_trees.csv')
    assert len(final_trees) == sum(len(tree) - 1 for tree in trees.values())
    assert {(r['net_id'], r['child']): r['parent'] for r in final_trees} == {
        (net, node): parent for net, tree in trees.items() for node, parent in tree.items() if parent is not None}
    assert checked_requests == set(migration)
    assert checked_transactions==set(transactions) and pending_group is None
    def sha(path):
        value=hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda:stream.read(1<<20),b""):value.update(block)
        return value.hexdigest()
    return dict(observed_read_rows_checked=observed_rows,remote_shadow_rows_checked=remote_rows,stale_proposals_checked=stale_proposals,fresh_replays_checked=fresh_replays,read_windows_checked=next_window,received_seed_rows_checked=len(seed_rows), received_task_requests_checked=len(checked_requests),
                schedule_mode=schedule_mode, epochs=len(iterations), backend_batches=batches,
                ripup_events=len(ripups), accepted_connections=len(trace), failed_connection_attempts=failures,
                cpu_legal=bool(legal), version_increments=model.increments,
                final_resources_and_costs_byte_equivalent=True,
                source_sha256={str(p.resolve()): sha(p) for p in source_files})
