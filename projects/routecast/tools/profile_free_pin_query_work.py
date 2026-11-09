"""Aggregate archived search counters; does not infer elapsed-time speedup."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

FIELDS = ('reverse_settled_nodes', 'reverse_examined_edges', 'labels_created',
          'labels_expanded', 'examined_edges')

def profile(rows):
    totals = Counter()
    by_status = {}
    cids = set()
    target_counts = []
    for row in rows:
        cid = row['cid']
        if type(cid) is not int or cid in cids:
            raise ValueError('duplicate or invalid connection ID')
        cids.add(cid)
        pins = set()
        target_counts.append(len(row['targets']))
        for result in row['targets']:
            pin = result['selected_ipin_ptc']
            if type(pin) is not int or pin in pins:
                raise ValueError('duplicate or invalid target pin')
            pins.add(pin)
            status = result['status']
            if status not in {'FOUND', 'UNREACHABLE', 'LABEL_LIMIT'}:
                raise ValueError('unknown query status')
            counters = by_status.setdefault(status, Counter())
            counters['queries'] += 1
            totals['queries'] += 1
            for field in FIELDS:
                value = result[field]
                if type(value) is not int or value < 0:
                    raise ValueError('invalid search counter')
                counters[field] += value
                totals[field] += value
    examined = totals['reverse_examined_edges'] + totals['examined_edges']
    return {'connections': len(cids), 'totals': dict(totals),
            'by_status': {s: dict(c) for s, c in sorted(by_status.items())},
            'targets_per_connection': {'min': min(target_counts, default=0),
                'max': max(target_counts, default=0),
                'mean': totals['queries']/len(cids) if cids else 0},
            'reverse_fraction_of_examined_arcs': totals['reverse_examined_edges']/examined if examined else 0,
            'scope': 'Archived arc-examination counts, not unique arcs, elapsed-time attribution, or a measured speedup. Repeated visits are counted separately.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    raw = args.input.read_bytes()
    result = profile(json.loads(raw))
    result['input_sha256'] = hashlib.sha256(raw).hexdigest()
    result['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
