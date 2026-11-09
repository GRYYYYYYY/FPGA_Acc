"""Independently reconstruct queued/in-flight byte credits and persistent task tickets."""
from collections import Counter, defaultdict, deque
import csv
import hashlib
from pathlib import Path
import struct


def audit(input_prefix, topology_prefix, output_prefix, slots, byte_limit, placement):
    assert slots > 0 and byte_limit >= 72 and placement in (1, 2)
    files = [Path(__file__).resolve()]

    def binary(prefix, suffix, layout):
        p = Path(str(prefix) + suffix)
        files.append(p)
        return list(struct.iter_unpack(layout, p.read_bytes()))

    def table(suffix):
        p = Path(str(output_prefix) + suffix)
        files.append(p)
        with p.open() as stream:
            return list(csv.DictReader(stream))

    tasks = {r[0]: r for r in binary(input_prefix, '.tasks', '<IIIIHHIII')}
    owners = [r[0] for r in binary(topology_prefix, '.node_die', '<H')]
    migration = {}
    for raw in table('.task_migration.csv'):
        row = {k: int(v) for k, v in raw.items()}
        key = (row['window'], row['task_id'])
        assert key not in migration and row['executed'] == 1
        t = tasks[row['task_id']]
        source = owners[t[2]]
        destination = owners[t[3]] if placement == 2 else source
        assert (row['source_die'], row['execution_die']) == (source, destination)
        assert row['encoded_envelope_bytes'] == 60 + 12 * row['seed_count'] and row['seed_count'] > 0
        migration[key] = row
    transactions = table('.transactions.csv')
    assert [(int(r['window']), int(r['task_id'])) for r in transactions] == list(migration)
    assert [int(r['epoch']) for r in transactions] == [r['epoch'] for r in migration.values()]
    active, accepted, queues = {}, set(), defaultdict(deque)
    live_bytes, live_entries = Counter(), Counter()
    counts, next_sequence, peak_bytes, peak_entries = Counter(), 0, 0, 0
    for row in table('.task_transfer_events.csv'):
        event = row.pop('event')
        r = {k: int(v) for k, v in row.items()}
        assert r['slot_limit'] == slots and r['byte_limit'] == byte_limit
        sequence, die, size = r['sequence'], r['destination_die'], r['encoded_bytes']
        key = (r['window'], r['task_id'])
        m = migration[key]
        assert (r['source_die'], die, r['epoch'], size) == (
            m['source_die'], m['execution_die'], m['epoch'], m['encoded_envelope_bytes'])
        ticket = (r['task_id'], r['epoch'], r['source_die'], die, r['window'], size)
        if event in ('enqueue', 'backpressure'):
            assert sequence == next_sequence and sequence <= 0xffffffff and key not in accepted
            fits = live_entries[die] < slots and size <= byte_limit - live_bytes[die]
            if event == 'backpressure':
                assert not fits and size <= byte_limit
            else:
                assert fits and sequence not in active
                next_sequence += 1
                active[sequence] = (ticket, 'queued')
                queues[die].append(sequence)
                accepted.add(key)
                live_bytes[die] += size
                live_entries[die] += 1
        elif event == 'receive':
            assert active[sequence] == (ticket, 'queued')
            assert queues[die] and queues[die].popleft() == sequence
            active[sequence] = (ticket, 'in_flight')
        elif event in ('complete', 'cancel'):
            assert active[sequence] == (ticket, 'in_flight' if event == 'complete' else 'queued')
            if event == 'cancel':
                queues[die].remove(sequence)
            del active[sequence]
            live_bytes[die] -= size
            live_entries[die] -= 1
        else:
            raise AssertionError(('unknown credit event', event))
        assert (r['live_bytes'], r['live_entries']) == (live_bytes[die], live_entries[die])
        assert 0 <= live_bytes[die] <= byte_limit and 0 <= live_entries[die] <= slots
        counts[event] += 1
        peak_bytes = max(peak_bytes, live_bytes[die])
        peak_entries = max(peak_entries, live_entries[die])
    assert not active and all(not q for q in queues.values())
    assert not any(live_bytes.values()) and not any(live_entries.values())
    assert accepted == set(migration)
    assert counts['enqueue'] == counts['receive'] == counts['complete'] == len(migration)
    assert counts['cancel'] == 0, 'successful routing cannot contain unexecuted cancelled tasks'
    return dict(status='actual_cpu_task_transfer_credit_lifecycles_reconstructed', events=dict(counts),
        peak_per_die_bytes=peak_bytes, peak_per_die_entries=peak_entries,
        final_credits_empty=True, tickets=next_sequence, source_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        scope='Exact queued/in-flight credits, persistent FIFO tickets, actual migration/ordered transaction identity. '
              'Encoded payload bound only;not process heap,search cost,physical network timing,seed-content oracle or asynchronous authority proof.',
        board_result=False, research_complete=False)
