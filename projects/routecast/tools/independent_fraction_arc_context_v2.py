"""Memoize exact electrical scalars only in owned immutable independent contexts."""
from fractions import Fraction
from types import MappingProxyType
from buffered_rc_node_classes import arc_delay as original_arc_delay
from independent_audit_context_v1 import load_context as original_load_context
_tables = {}
_calls = _hits = _misses = 0

def _register(classes, switches):
    if not isinstance(classes, tuple) or not isinstance(switches, MappingProxyType):
        raise TypeError('owned immutable independent electrical context required')
    if not all(isinstance(x, tuple) and len(x)==2 and all(isinstance(v,Fraction) for v in x) for x in classes):
        raise TypeError('exact immutable RC classes required')
    if not all(isinstance(x, tuple) and len(x)==2 and all(isinstance(v,Fraction) for v in x) for x in switches.values()):
        raise TypeError('exact immutable switch classes required')
    key = id(classes), id(switches)
    if key not in _tables:
        # Strong references prevent identity recycling. These objects originate in
        # original_load_context, whose backing mapping is privately owned.
        _tables[key] = (classes, switches, {})
    return key

def load_context(path, expected_digest):
    context = original_load_context(path, expected_digest)
    _register(context[2], context[3])
    return context

def arc_delay(classes, switches, node_class, switch_id):
    global _calls, _hits, _misses
    key = id(classes), id(switches)
    if key not in _tables:
        raise ValueError('unregistered independent electrical context')
    stored_classes, stored_switches, cache = _tables[key]
    assert stored_classes is classes and stored_switches is switches
    _calls += 1
    pair = node_class, switch_id
    if pair in cache:
        _hits += 1
        return cache[pair]
    value = original_arc_delay(classes, switches, node_class, switch_id)
    assert isinstance(value, Fraction)
    cache[pair] = value
    _misses += 1
    return value

def diagnostics():
    return dict(contexts=len(_tables), calls=_calls, hits=_hits, misses=_misses,
                entries=sum(len(x[2]) for x in _tables.values()),
                scope='Owned immutable graph electrical class/switch scalars only. No paths, predictions, budgets, ledger or event reuse; every original path and event body still executes.')
