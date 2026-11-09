"""Fixed-context query cost dependencies; caller owns synchronization and truth."""
from collections import defaultdict


class CostReadDependencyIndex:
    def __init__(self, context):
        self.context = context
        self.entries = {}
        self.readers = defaultdict(set)

    def discard(self, query_id):
        entry = self.entries.pop(query_id, None)
        if entry is None:
            return
        owner, footprint = entry
        for node in footprint:
            bucket = self.readers[node]
            bucket.remove(query_id)
            if not bucket:
                del self.readers[node]

    def register(self, query_id, owner, footprint):
        # Capture and validate before replacing an existing dependency record.
        nodes = frozenset(footprint)
        if any(type(n) is not int or n < 0 for n in nodes):
            raise ValueError('nonnegative integer cost node identities required')
        hash(query_id); hash(owner)
        self.discard(query_id)
        self.entries[query_id] = (owner, nodes)
        for node in nodes:
            self.readers[node].add(query_id)

    def invalidate(self, dirty, excluded_owner=None):
        nodes = frozenset(dirty)
        if any(type(n) is not int or n < 0 for n in nodes):
            raise ValueError('nonnegative integer dirty identities required')
        candidates = set()
        for node in nodes:
            candidates.update(self.readers.get(node, ()))
        doomed = {q for q in candidates
                  if excluded_owner is None or self.entries[q][0] != excluded_owner}
        for q in doomed:
            self.discard(q)
        return doomed

    def switch_context(self, context):
        if context == self.context:
            return set()
        removed = set(self.entries)
        self.entries.clear()
        self.readers.clear()
        self.context = context
        return removed
