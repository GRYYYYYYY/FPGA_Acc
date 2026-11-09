"""Current-arm resident topology adapter; no historical cache or independent XML audit."""
from array import array
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
from pre_route_endpoints import sha
from prepared_csr import TYPES
from streaming_prediction_audit import Nodes

class Edge:
    __slots__ = ('source', 'sink', 'switch_id')
    def __init__(self, source, sink, switch):
        self.source, self.sink, self.switch_id = source, sink, switch

class PhysicalEdges:
    def __init__(self, fields):
        self.dest = memoryview(fields['dest_ranks'].tobytes()).cast('Q')
        self.switch = memoryview(fields['switch_ids'].tobytes()).cast('Q')
        count = len(self.dest)
        n = len(fields['capacities'])
        rows = fields['row_offsets']
        if len(rows) != n+1 or rows[0] != 0 or rows[-1] != count or any(a > b for a,b in zip(rows,rows[1:])):
            raise ValueError('invalid resident CSR rows')
        if len(self.switch) != count or len(fields['edge_ids']) != count or any(v >= n for v in self.dest):
            raise ValueError('invalid resident edge arrays')
        self.slot = array('Q', [0]) * count
        sources = array('Q')
        seen = bytearray(count)
        for node in range(len(fields['capacities'])):
            degree = fields['row_offsets'][node+1] - fields['row_offsets'][node]
            sources.extend(array('Q', [node]) * degree)
        for slot, eid in enumerate(fields['edge_ids']):
            if eid >= count or seen[eid]:
                raise ValueError('original edge IDs must be a complete permutation')
            seen[eid] = 1
            self.slot[eid] = slot
        if len(sources) != count or not all(seen):
            raise ValueError('incomplete original edges')
        self.slot = memoryview(self.slot.tobytes()).cast('Q')
        self.sources = memoryview(sources.tobytes()).cast('Q')
    def __len__(self):
        return len(self.slot)
    def __getitem__(self, eid):
        if type(eid) is not int or not 0 <= eid < len(self):
            raise IndexError(eid)
        slot = self.slot[eid]
        return Edge(self.sources[slot], self.dest[slot], self.switch[slot])

class TupleEdges:
    def __init__(self, edges):
        self.raw = edges
    def __len__(self):
        return len(self.raw)
    def __getitem__(self, eid):
        e = self.raw[eid]
        return e.source, e.sink, e.switch_id

class Inventory:
    def __init__(self, path, digest, nodes, fields):
        self.path = Path(path)
        self.digest = digest
        self.validate(path, digest)
        if len(nodes) != len(fields['capacities']):
            raise ValueError('node scope mismatch')
        types = array('B')
        locations = {}
        for node, xml in enumerate(nodes):
            kind = xml.get('type')
            loc = xml.find('loc')
            if xml.get('id') != str(node) or kind not in TYPES or loc is None:
                raise ValueError('invalid resident node')
            if int(xml.get('capacity')) != fields['capacities'][node]:
                raise ValueError('resident capacity mismatch')
            types.append(TYPES[kind])
            locations[node] = (kind, MappingProxyType(dict(loc.attrib)))
        self.nodes = MappingProxyType(locations)
        edges = PhysicalEdges(fields)
        self.edges = TupleEdges(edges)
        self.graph = SimpleNamespace(
            nodes=Nodes(memoryview(types.tobytes()), memoryview(fields['capacities'].tobytes()).cast('Q')),
            edges=edges, sha256=digest)
        self.validate(path, digest)
    def validate(self, path, digest):
        if Path(path) != self.path or digest != self.digest or sha(self.path) != digest:
            raise ValueError('current graph identity changed')
