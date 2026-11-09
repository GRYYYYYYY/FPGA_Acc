"""Independent serial resource authority transitions for CPU trace replay."""
NONE = 0xffffffff
U64 = (1 << 64) - 1


def fnv_words(words):
    value = 1469598103934665603
    for word in words:
        assert 0 <= word <= U64
        for shift in range(0, 64, 8):
            value = ((value ^ ((word >> shift) & 255)) * 1099511628211) & U64
    return value


def route_hash(paths, order):
    return fnv_words(value for task in order for value in
                     (task, int(task in paths), len(paths.get(task, [])), *paths.get(task, [])))


class ResourceVersions:
    def __init__(self, initial):
        self.initial = tuple(tuple(r) for r in initial)
        self.state = [list(r) for r in initial]
        self.costs = [[r[2], r[3]] for r in initial]
        for row in self.state:
            row[2] = row[3] = 0
        self.owners = [set() for _ in initial]
        self.increments = dict(backend_commits=0, owner_refresh=0, global_cost=0)

    def clone(self):
        copy = object.__new__(ResourceVersions)
        copy.initial = self.initial
        copy.state = [list(r) for r in self.state]
        copy.costs = [list(r) for r in self.costs]
        copy.owners = [set(r) for r in self.owners]
        copy.increments = dict(self.increments)
        return copy

    def increment(self, node, kind):
        if self.state[node][4] == NONE:
            raise OverflowError('Resource version exhausted')
        self.state[node][4] += 1
        self.increments[kind] += 1

    def refresh(self, dirty):
        for node in sorted(dirty):
            base, actual = self.initial[node], self.state[node]
            known = set(self.owners[node])
            if base[0] and base[5] != NONE:
                known.add(base[5])
            occupancy = base[0] + sum(not (base[0] and base[5] == net) for net in self.owners[node])
            assert occupancy <= 65535
            owner = next(iter(known)) if occupancy == 1 and len(known) == 1 else NONE
            if (actual[0], actual[5]) != (occupancy, owner):
                self.increment(node, 'owner_refresh')
                actual[0], actual[5] = occupancy, owner

    def backend_commit(self, branch, net):
        assert len(branch) == len(set(branch))
        # The C++ backend preflights the whole candidate before its first write.
        changed = [node for node in branch if self.state[node][5] != net]
        if any(self.state[node][0] == 65535 or self.state[node][4] == NONE for node in changed):
            raise OverflowError('Backend commit preflight overflow')
        for node in changed:
            row = self.state[node]
            row[5] = net if row[0] == 0 else NONE
            row[0] += 1
            self.increment(node, 'backend_commits')

    def update_cost(self, present, history_step):
        next_costs = [[present, cost[1] + history_step * max(0, row[0] - row[1])]
                      for row, cost in zip(self.state, self.costs)]
        assert all(0 <= value <= U64 for cost in next_costs for value in cost)
        if any(new != old and row[4] == NONE
               for row, new, old in zip(self.state, next_costs, self.costs)):
            raise OverflowError('Cost update preflight overflow')
        for node, (new, old) in enumerate(zip(next_costs, self.costs)):
            if new != old:
                self.increment(node, 'global_cost')
        self.costs = next_costs

    def resource_hash(self):
        return fnv_words(value for row, cost in zip(self.state, self.costs)
                         for value in (row[0], row[1], cost[0], cost[1], row[4], row[5]))


def replay_private_versions(model, trial, tables, trees, paths, source, net_tasks, input_order):
    """Replay resource hashes after a separate path/predicate audit has passed."""
    assert trial['before_hash'] == model.resource_hash(), 'Pretrial resource hash differs'
    assert trial['before_route_hash'] == route_hash(paths, input_order)
    net, key = trial['net_id'], trial['trial']
    expected_owners = [set() for _ in model.state]
    for owner, tree in trees.items():
        for node, parent in tree.items():
            if parent is not None:
                expected_owners[node].add(owner)
    assert expected_owners == model.owners
    private = model.clone()
    private.refresh(range(len(private.state)))
    assert private.resource_hash() == trial['before_hash']
    dirty = set()
    for node, parent in trees[net].items():
        if parent is not None:
            private.owners[node].remove(net)
            dirty.add(node)
    private.refresh(dirty)
    assert private.resource_hash() == trial['ripup_hash'], 'Private ripup hash differs'
    private_tree = {source: None}
    private_paths = {task: path for task, path in paths.items() if task not in net_tasks}
    steps = [r for r in tables['net_trial_steps'] if r['trial'] == key]
    assert len(steps) == trial['steps']
    for position, step in enumerate(steps):
        assert step['step'] == position
        branch_rows = [r for r in tables['net_trial_branches'] if r['trial'] == key and r['step'] == position]
        assert [r['index'] for r in branch_rows] == list(range(step['branch_nodes']))
        branch = [r['node'] for r in branch_rows]
        success = step['candidate_present'] and step['search_status'] == 1 and step['commit_status'] == 4
        if success:
            private.backend_commit(branch, net)
        assert private.resource_hash() == step['backend_hash'], 'Private backend hash differs'
        if not success:
            assert position == len(steps) - 1
            assert step['owner_hash'] == step['backend_hash']
            break
        attachment = step['attachment']
        chain, node = [], attachment
        while node != source:
            assert node not in chain
            chain.append(node)
            node = private_tree[node]
        chain.reverse()
        parent = attachment
        for node in branch:
            assert node not in private_tree
            private_tree[node] = parent
            private.owners[node].add(net)
            parent = node
        private_paths[step['task_id']] = chain + branch
        private.refresh(branch)
        assert private.resource_hash() == step['owner_hash'], 'Private owner-refresh hash differs'
    assert private.resource_hash() == trial['private_hash'], 'Final private resource hash differs'
    attempted = {kind: private.increments[kind] - model.increments[kind] for kind in model.increments}
    if trial['accepted']:
        result_model = private
        result_trees = dict(trees)
        result_trees[net] = private_tree
        result_paths = private_paths
    else:
        result_model, result_trees, result_paths = model, trees, paths
    assert result_model.resource_hash() == trial['after_hash'], 'Published resource hash differs'
    assert route_hash(result_paths, input_order) == trial['after_route_hash'], 'Published route hash differs'
    return result_model, result_trees, result_paths, attempted
