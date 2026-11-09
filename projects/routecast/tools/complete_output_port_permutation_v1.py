"""Serialize an existing routed output permutation through a proven complete crossbar.

Only top-level output-port text changes. A full permutation preserves every
original driver token, including ignored and local-only nets. No route is changed.
"""
from collections import Counter
import re
import xml.etree.ElementTree as ET
from xml.parsers import expat
from xml.sax.saxutils import escape, unescape


def indices(text, count):
    if text is None:
        return range(count)
    values = list(map(int, text.split(':')))
    if len(values) == 1:
        result = values
    elif len(values) == 2:
        a, b = values
        result = range(a, b + (1 if b >= a else -1), 1 if b >= a else -1)
    else:
        raise ValueError('unsupported range')
    result = list(result)
    if not result or min(result) < 0 or max(result) >= count:
        raise ValueError('range outside declared port')
    return result


def complete_sources(pb, mode, port):
    """Require a single complete interconnect covering the entire output port."""
    output = [p for p in pb.findall('output') if p.get('name') == port]
    if len(output) != 1 or output[0].get('equivalent') != 'full':
        raise ValueError('output is not explicitly fully equivalent')
    width = int(output[0].get('num_pins'))
    scopes = [m for m in pb.findall('mode') if m.get('name') == mode] if mode else [pb]
    if len(scopes) != 1:
        raise ValueError('missing or ambiguous mode')
    scope = scopes[0]
    matches = []
    for interconnect in scope.findall('interconnect'):
        for edge in interconnect:
            destinations = edge.get('output', '').split()
            if any(re.fullmatch(re.escape(pb.get('name') + '.' + port) + r'(?:\[.*\])?', d)
                   for d in destinations):
                matches.append(edge)
    if len(matches) != 1 or matches[0].tag != 'complete':
        raise ValueError('output lacks a unique complete crossbar')
    edge = matches[0]
    destination = re.fullmatch(re.escape(pb.get('name') + '.' + port) + r'(?:\[([^\]]+)\])?', edge.get('output', ''))
    if not destination or set(indices(destination[1], width)) != set(range(width)):
        raise ValueError('crossbar does not cover the full output')
    children = {c.get('name'): c for c in scope.findall('pb_type')}
    sources = set()
    for token in edge.get('input', '').split():
        m = re.fullmatch(r'([^.[\]]+)(?:\[([^\]]+)\])?\.([^.[\]]+)(?:\[([^\]]+)\])?', token)
        if not m or m[1] not in children:
            raise ValueError('unsupported crossbar source')
        child = children[m[1]]
        ports = [p for p in child.findall('output') if p.get('name') == m[3]]
        if len(ports) != 1:
            raise ValueError('source is not a declared child output')
        for instance in indices(m[2], int(child.get('num_pb', '1'))):
            for bit in indices(m[4], int(ports[0].get('num_pins'))):
                source = f'{m[1]}[{instance}].{m[3]}[{bit}]->{edge.get("name")}'
                if source in sources:
                    raise ValueError('duplicate crossbar source')
                sources.add(source)
    if not sources:
        raise ValueError('empty crossbar')
    return width, sources


def permutation(tokens, required, allowed_sources):
    """Return new tokens and a bijection new-index -> old-index."""
    if not set(tokens) <= allowed_sources | {'open'}:
        raise ValueError('packed driver is not an allowed crossbar input')
    if any(type(k) is not int or type(v) is not int or not 0 <= k < len(tokens)
           or not 0 <= v < len(tokens) or tokens[v] == 'open' for k, v in required.items()):
        raise ValueError('invalid routed source assignment')
    if len(set(required.values())) != len(required):
        raise ValueError('one driver assigned to multiple output pins')
    assigned = dict(required)
    used = set(assigned.values())
    # Preserve original positions for every unconstrained token where possible.
    for i in range(len(tokens)):
        if i not in assigned and i not in used:
            assigned[i] = i
            used.add(i)
    remaining = iter(i for i in range(len(tokens)) if i not in used)
    for i in range(len(tokens)):
        if i not in assigned:
            assigned[i] = next(remaining)
    mapping = [assigned[i] for i in range(len(tokens))]
    if sorted(mapping) != list(range(len(tokens))):
        raise AssertionError('not a full permutation')
    output = [tokens[i] for i in mapping]
    assert Counter(output) == Counter(tokens)
    return output, mapping


def output_spans(data):
    """Exact byte spans for clustered output-port contents, without reformatting XML."""
    parser = expat.ParserCreate()
    stack = []
    block = None
    pending = None
    spans = {}
    def start(tag, attrs):
        nonlocal block, pending
        if tag == 'block' and len(stack) == 1:
            block = attrs['name']
        if tag == 'port' and stack == ['block', 'block', 'outputs']:
            key = (block, attrs['name'])
            if key in spans or pending is not None:
                raise ValueError('duplicate output port')
            begin = data.index(b'>', parser.CurrentByteIndex) + 1
            pending = (key, begin)
        stack.append(tag)
    def end(tag):
        nonlocal pending
        if tag == 'port' and stack == ['block', 'block', 'outputs', 'port']:
            key, begin = pending
            spans[key] = (begin, parser.CurrentByteIndex)
            pending = None
        assert stack.pop() == tag
    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.Parse(data, True)
    return spans


def rewrite(data, changes):
    spans = output_spans(data)
    edits = []
    for key, (old, new) in changes.items():
        a, b = spans[key]
        if (unescape(data[a:b].decode()).split() != old or Counter(old) != Counter(new)):
            raise ValueError('source bytes or driver multiset differ')
        edits.append((a, b, escape(' '.join(new)).encode()))
    output = []
    position = 0
    for a, b, replacement in sorted(edits):
        if a < position:
            raise ValueError('overlapping edits')
        output.extend([data[position:a], replacement])
        position = b
    output.append(data[position:])
    return b''.join(output)
