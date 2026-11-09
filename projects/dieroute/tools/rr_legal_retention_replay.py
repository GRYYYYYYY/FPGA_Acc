"""Independently reconstruct complete legal-connection retention and resource versions."""
from collections import defaultdict
import csv
import hashlib
from pathlib import Path
import struct
from rr_resource_version_replay import ResourceVersions, route_hash
import rr_resource_version_replay


def replay(input_prefix, output_prefix, schedule_mode, issue_width, min_timing_iterations,
           cost_scale=1, timing_weight=128, criticality_cap=64880, retention_mode=0):
    assert schedule_mode == 0 and issue_width > 0 and retention_mode in (0, 1)
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
    retention_events = table('legal_retention.csv')
    retention_connections = table('retention_connections.csv')
    if not retention_mode:
        assert not retention_events and not retention_connections
    next_retention = next_retained_connection = retained_occurrences = 0
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
        attempted = 0

        def ripup(net):
            nonlocal next_ripup, next_retention, next_retained_connection, retained_occurrences
            tree = trees[net]
            expected = dict(iteration=iteration, net_id=net, dispatch_batch=batch_index,
                            phase=schedule_mode, tree_nodes_before=len(tree),
                            routed_connections_before=sum(task in paths for task in net_tasks[net]))
            assert next_ripup < len(ripups) and ripups[next_ripup] == expected, 'Incorrect ripup dispatch or incumbent'
            next_ripup += 1
            kept_tasks, kept_nodes = set(), {roots[net]}
            eligible = retention_mode and pending[net] == 4 and len(net_tasks[net]) >= 16
            before_route = route_hash(paths, ids)
            before_routed = sum(task in paths for task in net_tasks[net])
            if eligible:
                for task in net_tasks[net]:
                    if task in paths and all(model.state[node][0] <= model.state[node][1] for node in paths[task]):
                        kept_tasks.add(task)
                        kept_nodes.update(paths[task])
            if retention_mode:
                for task in ordered[net]:
                    expected_connection = dict(iteration=iteration, net_id=net, task_id=task, retained=int(task in kept_tasks))
                    assert next_retained_connection < len(retention_connections) and retention_connections[next_retained_connection] == expected_connection, 'Retention decision disagrees with old path/occupancy'
                    next_retained_connection += 1
                retained_occurrences += len(kept_tasks)
            assert all(parent is None or parent in kept_nodes for node,parent in tree.items() if node in kept_nodes)
            dirty = set(tree) - kept_nodes
            for node in dirty:
                model.owners[node].remove(net)
            trees[net] = {node:parent for node,parent in tree.items() if node in kept_nodes}
            for task in net_tasks[net]:
                if task not in kept_tasks:
                    paths.pop(task, None)
            if retention_mode:
                expected_event = dict(iteration=iteration,net_id=net,reasons=pending[net],eligible=int(bool(eligible)),
                                      tree_nodes_before=len(tree),tree_nodes_after=len(kept_nodes),
                                      kept_connections=len(kept_tasks),dropped_connections=before_routed-len(kept_tasks),
                                      before_route_hash=before_route,after_route_hash=route_hash(paths,ids))
                assert next_retention < len(retention_events) and retention_events[next_retention] == expected_event, 'Retention event/cardinality/route checkpoint disagrees'
                next_retention += 1
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
                if retention_mode and net in cursors:
                    while cursors[net] < len(ordered[net]) and ordered[net][cursors[net]] in paths:
                        cursors[net] += 1
                if net in cursors and cursors[net] < len(ordered[net]):
                    wave.append(ordered[net][cursors[net]])
                    cursors[net] += 1
                    if schedule_mode == 2:
                        break
            if not wave:
                break
            for start in range(0, len(wave), expected_width):
                batch = wave[start:start + expected_width]
                attempted += len(batch)
                if schedule_mode:
                    dirty = set()
                    for task in batch:
                        net = tasks[task]['net']
                        if net not in started:
                            started.add(net)
                            if iteration:
                                dirty.update(ripup(net))
                    model.refresh(dirty)
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
                for task in sorted(proposals, key=lambda task: (tasks[task]['priority'], task)):
                    model.backend_commit(proposals[task][2], tasks[task]['net'])
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
        failed = attempted - len(seen)
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
    assert next_retention == len(retention_events) and next_retained_connection == len(retention_connections)
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
    return dict(legal_connection_retention=retention_mode, retention_events=len(retention_events), retained_connection_occurrences=retained_occurrences, schedule_mode=schedule_mode, epochs=len(iterations), backend_batches=batches,
                ripup_events=len(ripups), accepted_connections=len(trace), failed_connection_attempts=failures,
                cpu_legal=bool(legal), version_increments=model.increments,
                final_resources_and_costs_byte_equivalent=True,
                source_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files})
