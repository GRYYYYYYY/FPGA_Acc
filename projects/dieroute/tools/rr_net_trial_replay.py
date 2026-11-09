"""Independent private-net path/predicate replay. Resource-version replay is separate."""


def replay_trial(trial, tables, nodes, edges, initial, trees, paths, tasks, criticality,
                 cost_scale=1, timing_weight=128):
    net, iteration, key = trial['net_id'], trial['iteration'], trial['trial']
    assert trial['mode'] in (1, 2)
    assert all(trial[k] in (0, 1) for k in
               ('complete', 'delay_ok', 'wire_ok', 'capacity_ok', 'strict', 'accepted'))

    def selected(name):
        return [r for r in tables[name] if r['trial'] == key]

    def arc_delay(parent, child, minimum=False):
        begin, count, _ = nodes[parent]
        values = [delay for dst, cost, delay in edges[begin:begin + count] if dst == child]
        assert values, 'Trial contains a non-edge'
        return min(values) if minimum else values[0]

    def prefix(tree, node):
        chain, seen = [], set()
        while tree[node] is not None:
            assert node not in seen
            seen.add(node)
            chain.append(node)
            node = tree[node]
        return list(reversed(chain))

    def path_delay(task, path, minimum=True):
        parent, delay = tasks[task]['source'], 0
        for child in path:
            delay += arc_delay(parent, child, minimum)
            parent = child
        return delay

    def occupancy(all_trees):
        owners = [set() for _ in initial]
        for owner, tree in all_trees.items():
            for node, parent in tree.items():
                if parent is not None:
                    owners[node].add(owner)
        return [r[0] + sum(not (r[0] and r[5] == owner) for owner in owners[node])
                for node, r in enumerate(initial)]

    ids = sorted((task for task, t in tasks.items() if t['net_id'] == net),
                 key=lambda task: (-criticality[task], tasks[task]['priority'], task))
    assert ids and trial['connections'] == len(ids)
    assert all(task in paths for task in ids), 'Incomplete incumbent net'
    roots = {tasks[task]['source'] for task in ids}
    root, = roots
    old_tree = trees[net]
    assert old_tree[root] is None
    tree, private_paths = {root: None}, {}
    steps = selected('net_trial_steps')
    assert len(steps) == trial['steps'] <= len(ids)
    assert [r['step'] for r in steps] == list(range(len(steps)))
    complete = True
    for position, step in enumerate(steps):
        task = ids[position]
        assert step['task_id'] == task and step['net_id'] == net
        for field in ('source', 'sink', 'max_hops', 'priority', 'reserved'):
            assert step[field] == tasks[task][field], field
        assert step['criticality_q'] == criticality[task] and step['epoch'] == iteration
        submitted = [r for r in selected('net_trial_seeds') if r['step'] == position]
        assert [r['index'] for r in submitted] == list(range(step['seed_count']))
        expected = []
        for node in sorted(tree):
            chain = prefix(tree, node)
            delay = path_delay(task, chain, False)
            charge = ((delay * criticality[task] // 65535) * timing_weight // 256
                      if cost_scale == 1 else
                      delay * criticality[task] * cost_scale * timing_weight // (65535 * 256))
            expected.append((node, len(chain), charge))
        assert [(r['node'], r['hops'], r['cost_q']) for r in submitted] == expected, 'Incorrect submitted seeds'
        branch_rows = [r for r in selected('net_trial_branches') if r['step'] == position]
        assert [r['index'] for r in branch_rows] == list(range(step['branch_nodes']))
        branch = [r['node'] for r in branch_rows]
        success = bool(step['candidate_present'] and step['search_status'] == 1 and step['commit_status'] == 4)
        if not success:
            complete = False
            assert position == len(steps) - 1, 'Steps continue after a failed private search'
            break
        attachment = step['attachment']
        assert attachment in tree
        assert (branch[-1] if branch else attachment) == tasks[task]['sink']
        chain = prefix(tree, attachment)
        assert len(chain) + len(branch) <= tasks[task]['max_hops']
        parent = attachment
        for child in branch:
            assert child not in tree, 'Private branch re-enters existing tree'
            arc_delay(parent, child)
            tree[child] = parent
            parent = child
        private_paths[task] = chain + branch
    assert len(steps) == len(ids) or not complete, 'Truncated trial omits failed step'
    complete = complete and len(steps) == len(ids)
    assert trial['private_ripups'] == int(len(old_tree) > 1)
    assert trial['private_ripped_connections'] == len(ids)
    connection_rows = selected('net_trial_connections')
    path_rows = selected('net_trial_paths')
    assert len(connection_rows) == 2 * len(ids)
    before_epochs = {}
    for stage in (0, 1):
        entries = [r for r in connection_rows if r['stage'] == stage]
        assert [r['index'] for r in entries] == list(range(len(ids)))
        for task, row in zip(ids, entries):
            assert row['task_id'] == task and row['net_id'] == net
            for field in ('source', 'sink', 'max_hops', 'priority', 'reserved'):
                assert row[field] == tasks[task][field]
            assert row['criticality_q'] == criticality[task]
            if stage == 0:
                before_epochs[task] = row['epoch']
            else:
                assert row['epoch'] == (iteration if task in private_paths else before_epochs[task])
            state = paths if stage == 0 else private_paths
            stored = [r for r in path_rows if r['stage'] == stage and r['task_id'] == task]
            assert [r['index'] for r in stored] == list(range(row['path_nodes']))
            assert [r['node'] for r in stored] == state.get(task, [])
            assert row['routed'] == int(task in state)
            assert row['delay_ps'] == (path_delay(task, state[task]) if task in state else 0)
    assert all(r['step'] < len(steps) for name in ('net_trial_seeds', 'net_trial_branches') for r in selected(name))
    assert all(r['stage'] in (0, 1) and r['task_id'] in ids for r in path_rows)
    old_wire = sum(nodes[node][2] for node in old_tree)
    wire = sum(nodes[node][2] for node in tree)
    assert (trial['old_wire'], trial['trial_wire']) == (old_wire, wire)
    delay_ok = complete and all(path_delay(task, private_paths[task]) <= path_delay(task, paths[task]) for task in ids)
    strict = wire < old_wire or any(path_delay(task, path) < path_delay(task, paths[task]) for task, path in private_paths.items())
    replacement = dict(trees)
    replacement[net] = tree
    before_occ, after_occ = occupancy(trees), occupancy(replacement)
    capacity_ok = all(after <= max(before, initial[node][1]) for node, (before, after) in enumerate(zip(before_occ, after_occ)))
    accepted = complete and (trial['mode'] == 1 or (delay_ok and wire <= old_wire and capacity_ok and strict))
    expected_flags = dict(complete=complete, delay_ok=delay_ok, wire_ok=wire <= old_wire,
                          capacity_ok=capacity_ok, strict=strict, accepted=accepted)
    assert all(trial[k] == int(v) for k, v in expected_flags.items()), 'Incorrect trial acceptance predicates'
    if not accepted:
        assert trial['before_hash'] == trial['after_hash'] and trial['before_route_hash'] == trial['after_route_hash']
    published_paths = dict(paths)
    if accepted:
        published_paths.update(private_paths)
    return dict(trees=replacement if accepted else dict(trees), paths=published_paths,
                accepted=accepted, expanded=sum(r['expanded'] for r in steps),
                edge_visits=sum(r['edge_visits'] for r in steps),
                version_replay_verified=False)
