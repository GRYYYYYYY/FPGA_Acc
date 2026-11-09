"""Immutable RR metadata for native route export; not a routing algorithm/cache.

Build over every node/edge pair in the imported PR CSR, round-trip against the
existing XML reader, and retain ambiguous switch pairs for fail-closed lookup.
The enclosing bundle binds the database bytes before and after each candidate.
"""
from contextlib import closing
from dataclasses import fields
import hashlib
import json
from pathlib import Path
import sqlite3
import struct

SCHEMA = 'FUSIONPAR_RR_EXPORT_SQLITE_V1'
NODE_FIELDS = ('kind', 'xlow', 'ylow', 'xhigh', 'yhigh', 'layer', 'ptc', 'logical_pin')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def csr_scope(nodes_path, edges_path):
    nodes = list(struct.iter_unpack('<IHH', Path(nodes_path).read_bytes()))
    edges = list(struct.iter_unpack('<IHH', Path(edges_path).read_bytes()))
    pairs = set()
    cursor = 0
    for node, (begin, count, _) in enumerate(nodes):
        if begin != cursor or begin + count > len(edges):
            raise ValueError('RR cache requires complete contiguous CSR')
        for dst, _, _ in edges[begin:begin+count]:
            if dst >= len(nodes):
                raise ValueError('RR cache CSR destination outside node domain')
            pairs.add((node, dst))
        cursor += count
    if cursor != len(edges):
        raise ValueError('RR cache CSR has unreferenced edges')
    return set(range(len(nodes))), pairs


def chunks(values, size=500):
    values = sorted(values)
    for start in range(0, len(values), size):
        yield values[start:start+size]


def load(path, expected, used_nodes, used_edges, node_type):
    if expected.get('schema') != SCHEMA or tuple(f.name for f in fields(node_type)) != NODE_FIELDS:
        raise ValueError('unsupported RR cache/Node schema')
    nodes, switches, ambiguous = {}, {}, {}
    # immutable=1 avoids journals/locks; mode=ro forbids accidental writes.
    uri = Path(path).resolve().as_uri() + '?mode=ro&immutable=1'
    with closing(sqlite3.connect(uri, uri=True)) as db:
        rows = db.execute('SELECT key,value FROM metadata').fetchall()
        if len(rows) != 1 or rows[0][0] != 'manifest' or json.loads(rows[0][1]) != expected:
            raise ValueError('RR cache identity/coverage metadata mismatch')
        for group in chunks(used_nodes):
            sql = 'SELECT id,' + ','.join(NODE_FIELDS) + ' FROM nodes WHERE id IN (' + ','.join('?' for _ in group) + ')'
            for row in db.execute(sql, group):
                nodes[row[0]] = node_type(*row[1:])
        # Query outgoing rows in batches; filter to requested pairs in memory.
        # This retains the first XML switch and every conflicting alternative.
        for group in chunks({a for a, _ in used_edges}):
            sql = 'SELECT src,dst,switch_id,alternatives FROM edges WHERE src IN (' + ','.join('?' for _ in group) + ')'
            for src, dst, switch, alternatives in db.execute(sql, group):
                pair = (src, dst)
                if pair not in used_edges:
                    continue
                switches[pair] = switch
                if alternatives is not None:
                    values = json.loads(alternatives)
                    if not isinstance(values, list) or any(type(v) is not int or v < 0 for v in values):
                        raise ValueError('invalid RR switch alternatives')
                    choices = set(values)
                    if len(choices) != len(values) or len(choices) < 2 or switch not in choices:
                        raise ValueError('incomplete RR switch ambiguity')
                    ambiguous[pair] = choices
    if used_nodes - nodes.keys():
        raise ValueError('RR cache missing used nodes')
    if used_edges - switches.keys():
        raise ValueError('RR cache missing used edges')
    return nodes, switches, ambiguous


def build(graph, nodes_path, edges_path, output, writer):
    output = Path(output)
    if output.exists():
        raise ValueError('RR cache output already exists')
    if tuple(f.name for f in fields(writer.Node)) != NODE_FIELDS:
        raise ValueError('unsupported native Node schema')
    used_nodes, used_edges = csr_scope(nodes_path, edges_path)
    bindings = {name: {'path': str(Path(p).resolve()), 'sha256': sha(p)} for name, p in
                (('rr_graph', graph), ('csr_nodes', nodes_path), ('csr_edges', edges_path),
                 ('native_reader', writer.__file__), ('cache_implementation', __file__))}
    nodes, switches, ambiguous = writer.load_rr_graph(Path(graph), used_nodes, used_edges)
    metadata = {'schema': SCHEMA, 'bindings': bindings, 'node_count': len(nodes),
                'edge_pair_count': len(switches), 'ambiguous_pair_count': len(ambiguous)}
    # Refuse overwriting any artifact, even if another writer appears meanwhile.
    with output.open('xb'):
        pass
    with closing(sqlite3.connect(output)) as db:
        db.execute('CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL) WITHOUT ROWID')
        db.execute('CREATE TABLE nodes(id INTEGER PRIMARY KEY,kind TEXT NOT NULL,xlow INTEGER NOT NULL,ylow INTEGER NOT NULL,xhigh INTEGER NOT NULL,yhigh INTEGER NOT NULL,layer INTEGER NOT NULL,ptc INTEGER NOT NULL,logical_pin TEXT)')
        db.execute('CREATE TABLE edges(src INTEGER NOT NULL,dst INTEGER NOT NULL,switch_id INTEGER NOT NULL,alternatives TEXT,PRIMARY KEY(src,dst)) WITHOUT ROWID')
        db.execute('INSERT INTO metadata VALUES (?,?)', ('manifest', json.dumps(metadata, sort_keys=True)))
        db.executemany('INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?)',
            ((i, *(getattr(n, key) for key in NODE_FIELDS)) for i, n in sorted(nodes.items())))
        db.executemany('INSERT INTO edges VALUES (?,?,?,?)',
            ((a, b, s, json.dumps(sorted(ambiguous[a,b])) if (a,b) in ambiguous else None)
             for (a,b), s in sorted(switches.items())))
        db.commit()
    # Complete coverage, not a sample: every imported node and edge pair must
    # survive serialization with the exact original native-reader values.
    if load(output, metadata, used_nodes, used_edges, writer.Node) != (nodes, switches, ambiguous):
        raise ValueError('RR cache round-trip differs from native XML reader')
    for entry in bindings.values():
        if sha(entry['path']) != entry['sha256']:
            raise ValueError('RR cache source changed during preparation')
    output.chmod(0o444)
    return metadata
