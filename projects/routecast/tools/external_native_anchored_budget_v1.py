"""Prospective proxy budget rule; caller must certify source paths before use.

No STA/slack interpretation. Unchanged means SOURCE/SINK pair equality within
one graph, preserving CID and NET identity. Changed siblings use current floors.
"""
POLICY = 'NATIVE_ENDPOINT_ANCHORED_PROXY_V2'

def _integer(value, name, positive=False):
    if type(value) is not int or value < int(positive):
        raise ValueError(name)
    return value

def assign(source_rows, current_rows, source_graph_sha256, current_graph_sha256,
           scale):
    _integer(scale, 'scale', True)
    if (not isinstance(source_graph_sha256, str) or
        len(source_graph_sha256) != 64 or
        any(c not in '0123456789abcdef' for c in source_graph_sha256) or
        source_graph_sha256 != current_graph_sha256):
        raise ValueError('same certified graph required')
    def index(rows, source):
        result = {}
        for row in rows:
            for key in ('connection_id', 'net_id', 'source', 'sink', 'floor_integer'):
                _integer(row[key], key)
            cid = row['connection_id']
            if cid in result:
                raise ValueError('duplicate CID')
            if source:
                delay = _integer(row['answer']['delay'], 'source delay')
                if delay < row['floor_integer']:
                    raise ValueError('source delay below source floor')
            result[cid] = row
        return result
    old, current = index(source_rows, True), index(current_rows, False)
    if not current or old.keys() != current.keys():
        raise ValueError('complete identical CID universe required')
    result = []
    for cid, row in sorted(current.items()):
        previous = old[cid]
        if previous['net_id'] != row['net_id']:
            raise ValueError('CID NET identity changed')
        same = (previous['source'], previous['sink']) == (row['source'], row['sink'])
        floor = row['floor_integer']
        if same and floor != previous['floor_integer']:
            raise ValueError('same graph/pair floor conflict')
        # Integer ceil(scale * 1ns), avoiding assumptions about scale divisibility.
        proxy = max((scale + 10**9 - 1)//10**9, (3*floor + 1)//2)
        budget = max(proxy, previous['answer']['delay']) if same else proxy
        result.append(dict(connection_id=cid, net_id=row['net_id'],
                           floor_integer=floor, proxy_budget_integer=proxy,
                           budget_integer=budget, unchanged_endpoint_pair=same))
    return result
