"""Fixed pool metadata and dirty-node excess updates; caller supplies complete dirty set."""
from collections import defaultdict
from fractions import Fraction
from pooled_channel_pressure import KEYS, payload


class PooledPressure:
    def __init__(self, fields):
        self.types = tuple(fields['types'])
        self.capacities = tuple(fields['capacities'])
        self.groups = defaultdict(list)
        self.node_group = {}
        for node, cap in enumerate(self.capacities):
            if self.types[node] in (4, 5) and cap > 0:
                key = tuple(fields[name][node] for name in KEYS)
                self.groups[key].append(node)
                self.node_group[node] = key
        self.group_capacity = {key: sum(self.capacities[n] for n in nodes)
                               for key, nodes in self.groups.items()}
        self.node_excess = {}
        self.group_excess = {}
        self.rows = {}

    def fork(self):
        """Share fixed metadata; copy all mutable pressure state for publication staging."""
        branch = object.__new__(PooledPressure)
        for name in ('types', 'capacities', 'groups', 'node_group', 'group_capacity'):
            setattr(branch, name, getattr(self, name))
        for name in ('node_excess', 'group_excess', 'rows'):
            setattr(branch, name, dict(getattr(self, name)))
        return branch

    def refresh(self, occupancy, dirty_nodes):
        changes, deltas = {}, defaultdict(int)
        for node in set(dirty_nodes):
            if type(node) is not int or not 0 <= node < len(self.types):
                raise ValueError('invalid dirty node')
            used = occupancy.get(node, 0)
            if type(used) is not int or used < 0:
                raise ValueError('invalid occupancy')
            if node in self.node_group:
                excess = max(0, used - self.capacities[node])
                changes[node] = excess
                deltas[self.node_group[node]] += excess - self.node_excess.get(node, 0)
        totals, staged_rows = {}, {}
        for key, delta in deltas.items():
            total = self.group_excess.get(key, 0) + delta
            if total < 0:
                raise ValueError('pool excess underflow')
            totals[key] = total
            value = 1 + Fraction(total, self.group_capacity[key])
            for node in self.groups[key]:
                staged_rows[node] = (self.capacities[node], value) if total else None
        # Complete validation and construction precede state publication.
        for node, excess in changes.items():
            if excess:
                self.node_excess[node] = excess
            else:
                self.node_excess.pop(node, None)
        for key, total in totals.items():
            if total:
                self.group_excess[key] = total
            else:
                self.group_excess.pop(key, None)
        for node, row in staged_rows.items():
            if row is None:
                self.rows.pop(node, None)
            else:
                self.rows[node] = row
        return {'dirty_nodes': len(changes), 'affected_groups': len(totals),
                'refreshed_group_members': len(staged_rows)}

    def payload(self, digest):
        return payload(len(self.types), digest, self.rows)
