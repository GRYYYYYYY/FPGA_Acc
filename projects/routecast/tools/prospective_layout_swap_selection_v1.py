"""Outcome-blind deterministic disjoint swaps from admitted physical site records.

Caller must bind source placement and RR-derived site records to the same graph
and netlist epoch. Selection does not certify those external identities.
"""
def select_swaps(blocks, count=3):
    if type(count) is not int or count < 0:
        raise ValueError('invalid requested swap count')
    records = {}
    occupied = set()
    for row in blocks:
        if set(row) != {'name', 'logical_type', 'location', 'physical_type', 'subtile'}:
            raise ValueError('unexpected block record schema')
        name, location = row['name'], tuple(row['location'])
        if not isinstance(name, str) or not name or name in records:
            raise ValueError('invalid or duplicate block name')
        if len(location) != 4 or any(type(x) is not int or x < 0 for x in location):
            raise ValueError('invalid x/y/subtile/layer location')
        if location in occupied:
            raise ValueError('duplicate occupied site')
        if type(row['subtile']) is not int or row['subtile'] != location[2]:
            raise ValueError('subtile identity mismatch')
        if any(not isinstance(row[k], str) or not row[k] for k in ['logical_type', 'physical_type']):
            raise ValueError('missing logical or physical type')
        records[name] = dict(row, location=location)
        occupied.add(location)
    eligible = sorted(n for n, r in records.items() if r['logical_type'] == 'clb')
    used, swaps = set(), []
    for i, left in enumerate(eligible):
        if len(swaps) == count:
            break
        if left in used:
            continue
        a = records[left]
        for right in eligible[i+1:]:
            if right in used:
                continue
            b = records[right]
            if (a['physical_type'], a['subtile']) != (b['physical_type'], b['subtile']):
                continue
            swaps.append({'blocks': [left, right], 'source_locations': [list(a['location']), list(b['location'])], 'physical_type': a['physical_type'], 'subtile': a['subtile']})
            used.update([left, right])
            break
    return {'requested': count, 'selected': len(swaps), 'unavailable': count-len(swaps), 'swaps': swaps,
            'episode_semantics': 'Each swap is applied independently to the same source placement; all other locations remain unchanged. Caller must verify full physical pin and placement legality.'}
