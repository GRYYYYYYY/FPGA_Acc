"""Replay adaptive decision scores,admission loads and transfer credit lifecycles."""
from collections import Counter, defaultdict, deque
import csv
import hashlib
from pathlib import Path
import struct


def audit(input_prefix, topology_prefix, output_prefix, slots, byte_limit, placement):
    assert slots > 0 and byte_limit >= 72 and placement in (1, 2, 3)
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
    decisions = {}
    epoch_q = {}
    if placement == 3:
        for raw in table('.migration_decisions.csv'):
            r = {k:int(v) for k,v in raw.items()}
            key = (r['window'],r['task_id'])
            assert key not in decisions
            t = tasks[r['task_id']]
            assert (r['source_die'],r['sink_die']) == (owners[t[2]],owners[t[3]])
            epoch = r['epoch']
            if epoch not in epoch_q:
                epoch_q[epoch] = {int(x['task_id']):int(x['criticality_q']) for x in table(f'.timing_iteration_{epoch}.input.csv')}
            q = r['criticality_q']
            assert q == epoch_q[epoch][r['task_id']] and 0 <= q <= 65535
            values = {}
            for side in ['source','sink']:
                entries,bytes_,limit,pressure = [r[side+'_'+k] for k in ['entries','bytes','byte_limit','pressure']]
                assert limit == byte_limit and 0 <= bytes_ <= limit and 0 <= entries <= slots and 0 <= pressure <= 65535
                die = r[side+'_die']
                locality = ((q<<8)//65535 if die != r['sink_die'] else 0) + (((65535-q)<<8)//65535 if die != r['source_die'] else 0)
                values[side] = (entries<<8) + (bytes_<<8)//limit + pressure*(65535-q)//65535 + locality
                assert r[side+'_score'] == values[side]
            selected = r['sink_die'] if values['sink'] < values['source'] else r['source_die']
            assert r['selected_die'] == selected
            decisions[key] = r
    migration = {}
    positions = Counter()
    for raw in table('.task_migration.csv'):
        row = {k: int(v) for k, v in raw.items()}
        key = (row['window'], row['task_id'])
        assert key not in migration and row['executed'] == 1
        t = tasks[row['task_id']]
        source = owners[t[2]]
        destination = decisions[key]['selected_die'] if placement == 3 else (owners[t[3]] if placement == 2 else source)
        assert (row['source_die'], row['execution_die']) == (source, destination)
        position_key = (row['window'], destination)
        assert row['queue_position'] == positions[position_key]
        positions[position_key] += 1
        assert row['encoded_envelope_bytes'] == 60 + 12 * row['seed_count'] and row['seed_count'] > 0
        migration[key] = row
    transactions = table('.transactions.csv')
    assert [(int(r['window']), int(r['task_id'])) for r in transactions] == list(migration)
    assert [int(r['epoch']) for r in transactions] == [r['epoch'] for r in migration.values()]
    active, accepted, queues = {}, set(), defaultdict(deque)
    live_bytes, live_entries = Counter(), Counter()
    counts, next_sequence, peak_bytes, peak_entries = Counter(), 0, 0, 0
    decision_loads_checked = set()
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
        if placement == 3 and key not in decision_loads_checked:
            assert event in ('enqueue','backpressure')
            decision_loads_checked.add(key)
            d = decisions[key]
            for side in ['source','sink']:
                observed = d[side+'_die']
                assert (d[side+'_entries'],d[side+'_bytes']) == (live_entries[observed],live_bytes[observed])
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
    if placement == 3:assert set(decisions) == accepted == decision_loads_checked
    assert counts['enqueue'] == counts['receive'] == counts['complete'] == len(migration)
    assert counts['cancel'] == 0, 'successful routing cannot contain unexecuted cancelled tasks'
    return dict(status='adaptive_migration_scores_admission_loads_and_credits_reconstructed', decision_requests_checked=len(decisions), events=dict(counts),
        peak_per_die_bytes=peak_bytes, peak_per_die_entries=peak_entries,
        final_credits_empty=True, tickets=next_sequence, source_sha256={str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        scope='Exact queued/in-flight credits, persistent FIFO tickets, actual migration/ordered transaction identity. '
              'Decision scores and actual admission loads verified against STA q andcredit events. Pressure inputs logged by authoritative dispatcher;independent fullboundarypressure reconstruction remains open. Notphysicalperformance,policyoptimality orhardwareproof.',
        board_result=False, research_complete=False)
