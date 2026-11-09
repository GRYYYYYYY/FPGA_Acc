"""Transactional endpoint HPWL proxy; no routing or STA guarantee."""
from collections import defaultdict


def index_rows(rows):
    result = {}
    for row in rows:
        values = tuple(row[k] for k in ('connection_id', 'net_id', 'source', 'sink'))
        if any(type(x) is not int or x < 0 for x in values):
            raise ValueError('nonnegative integer IDs required')
        cid, net, source, sink = values
        if cid in result:
            raise ValueError('duplicate connection')
        result[cid] = (net, source, sink)
    return result


def span(records, locations):
    points = [locations[node] for _, source, sink in records for node in (source, sink)]
    return sum(max(p[d] for p in points) - min(p[d] for p in points) for d in (0, 1))


class GeometryState:
    def __init__(self, rows, locations):
        self.locations = dict(locations)
        self.rows = index_rows(rows)
        self.nets = defaultdict(dict)
        for cid, record in self.rows.items():
            self.nets[record[0]][cid] = record
        self.spans = {net: span(records.values(), self.locations) for net, records in self.nets.items()}
        self.total = sum(self.spans.values())
        self.epoch = 0

    def trial(self, replacements, epoch):
        if type(epoch) is not int or epoch != self.epoch:
            raise ValueError('stale epoch')
        changes = index_rows(replacements)
        if any(cid not in self.rows or record[0] != self.rows[cid][0] for cid, record in changes.items()):
            raise ValueError('unknown connection or changed NET identity')
        dirty = {record[0] for cid, record in changes.items() if record != self.rows[cid]}
        nets = {net: dict(self.nets[net]) for net in dirty}
        for cid, record in changes.items():
            if record[0] in dirty:
                nets[record[0]][cid] = record
        spans = {net: span(records.values(), self.locations) for net, records in nets.items()}
        total = self.total + sum(spans[n] - self.spans[n] for n in dirty)
        # Nothing mutates until every endpoint has been resolved.
        return {'epoch': epoch, 'changes': changes, 'nets': nets, 'spans': spans, 'total': total, 'dirty': sorted(dirty)}

    def update(self, replacements, epoch):
        trial = self.trial(replacements, epoch)
        self.rows.update(trial['changes'])
        self.nets.update(trial['nets'])
        self.spans.update(trial['spans'])
        self.total = trial['total']
        self.epoch += 1
        return trial
