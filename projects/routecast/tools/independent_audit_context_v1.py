"""Process-local independent XML context; no prediction/model/historical state reuse."""
from pathlib import Path
from types import MappingProxyType
from time import perf_counter
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read
from pre_route_endpoints import sha
_contexts = {}
_loads = 0
_calls = 0
_load_seconds = 0.0

def load_context(path, expected_digest):
    global _loads, _calls, _load_seconds
    path = Path(path).resolve()
    if sha(path) != expected_digest:
        raise ValueError('graph digest changed before independent audit context access')
    key = (str(path), expected_digest)
    _calls += 1
    if key not in _contexts:
        start = perf_counter()
        xml = ImmutableXMLAudit(path, expected_digest)
        ids, classes, switches, digest = read(path)
        if digest != expected_digest or len(ids) != len(xml.types):
            raise ValueError('electrical/topology context mismatch')
        ids = memoryview(ids.tobytes()).cast('Q')
        context = (xml, ids, tuple(classes), MappingProxyType(dict(switches)), digest)
        if sha(path) != expected_digest:
            raise ValueError('graph changed during independent context construction')
        _contexts[key] = context
        _loads += 1
        _load_seconds += perf_counter() - start
    return _contexts[key]

def diagnostics():
    return dict(contexts=len(_contexts), context_loads=_loads, accesses=_calls,
                independent_xml_parses=2*_loads, load_seconds=_load_seconds,
                scope='Topology and electrical readers retained separately; only immutable graph inputs shared within one process. All paths/events/ledgers rechecked.')
