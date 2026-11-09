"""Independent decoder/replay for serial native label RPC captures.

This verifies captured remote label operations, not local heap execution or
concurrent delivery. Authority summaries and arbitration use separate channels.
"""
import csv
import hashlib
import mmap
import struct
from collections import defaultdict

NONE = (1 << 32)-1
MAX = (1 << 64)-1
FIELDS = ('probes', 'probe_protected', 'relaxes', 'accepted', 'rejected', 'traces', 'epoch_rejects')


def crc64(data):
    table = []
    for byte in range(256):
        value = byte << 56
        for _ in range(8):
            value = ((value << 1) ^ (0x42f0e1eba9ea3693 if value >> 63 else 0)) & MAX
        table.append(value)
    value = 0
    for byte in data:
        value = table[(value >> 56) ^ byte] ^ ((value << 8) & MAX)
    return value


def decode(words):
    epoch, request, header, cost, priority, ancestry, resource, version = words
    return dict(epoch=epoch, request=request, node=header & NONE,
                op=(header >> 32) & 255, sender=(header >> 40) & 255,
                receiver=(header >> 48) & 255, status=header >> 56,
                cost=cost, priority=priority, hops=ancestry & NONE,
                parent=ancestry >> 32, edge=resource & NONE,
                flags=resource >> 32, version=version)


def label(p):
    return (p['cost'], p['hops'], p['parent'], p['edge'], p['flags'], p['version'])


class LabelTransportAudit:
    def __init__(self, route, command, enabled):
        binary, summary = route/'worker_packets.bin', route/'worker_transport.csv'
        self.present = binary.exists()
        assert self.present == summary.exists(), 'incomplete label transport capture'
        self.enabled = enabled
        self.limit = int(command[8])
        self.groups = {}
        self.summaries = defaultdict(list)
        self.total = defaultdict(int)
        self.per_die = defaultdict(lambda: defaultdict(int))
        self.file = self.data = None
        if not self.present:
            return  # Older evidence did not record this protocol.
        with summary.open() as stream:
            for row in csv.DictReader(stream):
                row = {k: int(v) for k, v in row.items()}
                assert all(v >= 0 for v in row.values())
                self.summaries[tuple(row[k] for k in ('repeat', 'search', 'replay', 'attempt'))].append(row)
        self.file = binary.open('rb')
        assert binary.stat().st_size >= 64
        self.data = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
        data = self.data
        magic, major, minor, kind, count, size, arch, crc, flags = struct.unpack_from('<8sHHIQQ16sQQ', data)
        assert (magic, major, minor, kind, flags) == (b'FPGAACCP', 0, 1, 0x44520020, 1)
        assert arch.hex() == command[6] and count*128 == size == len(data)-64
        payload = memoryview(data)[64:]
        assert crc64(payload) == crc, 'label capture CRC64'
        payload.release()
        assert enabled or (count == 0 and not self.summaries)
        repeats = int(command[11])
        hashes = [hashlib.sha256() for _ in range(repeats)]
        origins = {}
        previous_key = None
        previous_epoch = 0
        for index in range(count):
            offset = 64+index*128
            prefix = struct.unpack_from('<8Q', data, offset)
            key = prefix[:4]
            rep = key[0]
            assert 0 <= rep < repeats and prefix[5:] == (0, 0, 0)
            words = struct.unpack_from('<8Q', data, offset+64)
            epoch = words[0]
            if key != previous_key:
                assert previous_key is None or key > previous_key
                assert prefix[4] == 0 and epoch > previous_epoch
                self.groups[key] = [offset, 0]
                previous_key, previous_epoch = key, epoch
            assert epoch == previous_epoch and prefix[4] == self.groups[key][1]
            self.groups[key][1] += 1
            origins.setdefault(rep, epoch)
            # Search epochs persist across repetitions. Normalize only their
            # origin; all relative epochs, IDs, payloads and ordering must match.
            hashes[rep].update(struct.pack('<7Q', *prefix[1:]))
            hashes[rep].update(struct.pack('<8Q', epoch-origins[rep], *words[1:]))
        assert len({h.digest() for h in hashes}) == 1, 'non-deterministic label traffic'
        self.normalized_sha256 = hashes[0].hexdigest()
        self.capture_records = count

    def plan(self, key, first, plan, dies, queues, path, member, tree, sink, arc_ok, allowed, step_cost):
        if not self.present or not self.enabled:
            return
        summary = self.summaries.pop(key)
        assert [r['die'] for r in summary] == list(range(dies))
        order = [p['die'] for p in plan]
        active = set(order)
        offset, count = self.groups.pop(key, (0, 0))
        assert count % 2 == 0, 'unanswered label request'
        observed = {}
        counters = {die: dict.fromkeys(FIELDS, 0) for die in range(dies)}
        pending = None
        last_id = 0
        trace = []
        tracing = False

        def owner(n):
            mask = member(n)
            assert mask and mask.bit_count() <= 2
            if n == sink:
                assert mask & (1 << order[-1])
                return order[-1]
            if n in tree:
                assert mask & (1 << order[0])
                return order[0]
            if mask & (mask-1):
                for a, b in zip(order, order[1:]):
                    if mask == (1 << a) | (1 << b):
                        return b
                raise AssertionError('boundary outside corridor')
            die = mask.bit_length()-1
            assert die in active
            return die

        def observe(p):
            n = p['node']
            current = label(p)
            # Every incoming update of an internal monotone boundary crosses
            # workers. Only its local close is absent from the wire capture.
            # Sink labels may also have local incoming edges, so exclude them.
            if n == sink or n in tree or not member(n) & (member(n)-1):
                return
            old = observed.get(n, (MAX, NONE, NONE, NONE, 0, 0))
            closed = (*old[:4], old[4] | 2, old[5]+1)
            assert current == old or (old[4] & 1 and not old[4] & 2 and current == closed), 'unlogged boundary label mutation'
            observed[n] = current

        for index in range(0, count, 2):
            request_words = struct.unpack_from('<8Q', self.data, offset+index*128+64)
            reply_words = struct.unpack_from('<8Q', self.data, offset+(index+1)*128+64)
            q, r = decode(request_words), decode(reply_words)
            op, n, sender, receiver = q['op'], q['node'], q['sender'], q['receiver']
            assert op in (1, 3, 5) and q['status'] == 0 and q['request'] > 0
            assert receiver < dies and receiver == owner(n) and allowed(n)
            assert (r['epoch'], r['request'], r['node'], r['op'], r['sender'], r['receiver']) == (q['epoch'], q['request'], n, op+1, receiver, sender)
            metrics = counters[receiver]
            if op in (1, 5):
                assert request_words[3:] == (0, 0, 0, 0, 0)
                assert q['request'] > last_id
                last_id = q['request']
                assert r['status'] == 0 and r['priority'] == 0 and r['flags'] & ~7 == 0
                if r['flags'] & 1:
                    assert r['cost'] < MAX and r['version'] > 0
                else:
                    assert label(r) == (MAX, NONE, NONE, NONE, 0, 0)
                observe(r)
                if op == 1:
                    assert not tracing and sender in active and sender != receiver and n not in tree
                    assert member(n) & (1 << sender) and member(n) & (1 << receiver)
                    assert order.index(receiver) == order.index(sender)+1
                    metrics['probes'] += 1
                    metrics['probe_protected'] += bool(r['flags'] & 6)
                    pending = (q, r)
                else:
                    assert sender == 8 and first['completed']
                    tracing = True
                    trace.append(r)
                    metrics['traces'] += 1
            else:
                assert not tracing and pending is not None
                probe, snapshot = pending
                assert (q['request'], n, sender, receiver) == (probe['request'], probe['node'], probe['sender'], probe['receiver'])
                pending = None
                assert q['version'] == snapshot['version'] and not snapshot['flags'] & 6
                assert q['cost'] <= q['priority'] < MAX and q['hops'] > 0 and q['flags'] == 0
                assert q['parent'] != n and owner(q['parent']) == sender
                assert arc_ok(q['parent'], n, q['edge']) == sender
                assert (q['cost'], q['hops'], q['parent'], q['edge']) < label(snapshot)[:4]
                assert reply_words[3:6] == (0, 0, 0) and r['edge'] == 0
                metrics['relaxes'] += 1
                if r['status'] == 1:
                    assert r['flags'] == (0 if snapshot['flags'] & 1 else 8)
                    assert q['version'] < MAX and r['version'] == q['version']+1
                    observed[n] = (q['cost'], q['hops'], q['parent'], q['edge'], 1, r['version'])
                    metrics['accepted'] += 1
                else:
                    # No intervening local execution occurs during a serial RPC.
                    assert r['status'] == 5 and not snapshot['flags'] & 1
                    assert r['flags'] == 0 and r['version'] == snapshot['version']
                    assert first['search_status'] == 2
                    assert sum(row['labels'] for row in queues) == self.limit
                    metrics['rejected'] += 1
        if first['completed'] and dies > 1:
            attachment = first['attachment']
            depth = tree[attachment][2]
            expected = [(attachment, 0, depth, NONE, NONE, 7)]
            cost = 0
            for index, edge in enumerate(path, 1):
                cost += step_cost(edge['destination'])
                expected.append((edge['destination'], cost, depth+index, edge['source'], edge['pip_key'], 3))
            actual = [(p['node'], p['cost'], p['hops'], p['parent'], p['edge'], p['flags']) for p in trace]
            assert actual == list(reversed(expected)), 'label traceback differs from physical candidate'
        else:
            assert not trace
        for row, queue in zip(summary, queues):
            die = row['die']
            assert all(row[k] == counters[die][k] for k in FIELDS), 'transport counters differ from packets'
            assert counters[die]['accepted'] == queue['transfers']
            assert counters[die]['relaxes'] == counters[die]['accepted']+counters[die]['rejected']
            for field in FIELDS:
                self.total[field] += row[field]
                self.per_die[die][field] += row[field]
        self.total['packets'] += count

    def finish(self):
        assert not self.groups and not self.summaries, 'unconsumed label capture'
        if self.present:
            assert self.total['packets'] == self.capture_records
            assert self.total['packets'] == 2*sum(self.total[k] for k in ('probes', 'relaxes', 'traces'))
        if self.data is not None:
            self.data.close()
            self.file.close()
        return dict(capture_present=self.present, verified=bool(self.present and self.enabled),
                    totals=dict(self.total), per_die={str(d): dict(v) for d, v in self.per_die.items()},
                    payload_bytes=64*self.total['packets'],
                    normalized_repeat_sha256=getattr(self, 'normalized_sha256', None),
                    limits='Serial remote probes/updates and controller traceback only; excludes arbitration, seeds, authority summaries, local queue execution and physical transport overhead. Not concurrent or hardware traffic evidence.')
