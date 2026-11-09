"""Resolve packed local references to atom NET tokens; no route input."""
import re

REF = re.compile(r'^([^.]*)\.([^.[\]]+)\[(\d+)\]$')


class Resolver:
    def __init__(self, root):
        self.parents = {child: parent for parent in root.iter('block') for child in parent.findall('block')}
        self.memo = {}

    def resolve(self, block, port, index, active=frozenset()):
        key = (block, port, index)
        if key in active:
            raise ValueError('packed pin reference cycle')
        if key in self.memo:
            return self.memo[key]
        ports = [p for section in ('inputs', 'outputs', 'clocks') for p in block.findall(section + '/port')
                 if p.get('name') == port]
        if len(ports) != 1:
            raise ValueError('missing or ambiguous port')
        tokens = (ports[0].text or '').split()
        if type(index) is not int or not 0 <= index < len(tokens):
            raise ValueError('packed index out of range')
        token = tokens[index]
        if token == 'open':
            value = None
        elif '->' not in token:
            value = token
        else:
            m = REF.fullmatch(token.split('->', 1)[0])
            if m is None:
                raise ValueError('unsupported packed reference')
            instance, name, bit = m[1], m[2], int(m[3])
            matches = [c for c in block.findall('block') if c.get('instance') == instance]
            if not matches:
                current = block
                while current is not None:
                    own = current.get('instance')
                    if instance in {own, re.sub(r'\[\d+\]$', '', own)}:
                        matches = [current]
                        break
                    current = self.parents.get(current)
            if len(matches) != 1:
                raise ValueError('missing or ambiguous packed context')
            value = self.resolve(matches[0], name, bit, active | {key})
        self.memo[key] = value
        return value
