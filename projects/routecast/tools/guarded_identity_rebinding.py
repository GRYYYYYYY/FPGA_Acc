"""Conservative identity rebinding candidate; caller must bind native provenance.

Requires identical packed NET externally, unchanged subtile/block ids, identical
root tile type, and matching physical pin/class in the same RR graph. Does not
certify native logical equivalence or authorize canonical post-routing reuse.
"""
import copy

def rebind_identity(table, old_place, new_place, maps):
    types, grid, endpoints = maps
    if set(old_place) != set(new_place):
        raise ValueError('block set changed')
    for block, old in old_place.items():
        new = new_place[block]
        if old[2] != new[2] or old[4] != new[4]:
            raise ValueError('subtile/block identity changed')
        a = grid.get((old[0], old[1], old[3]))
        b = grid.get((new[0], new[1], new[3]))
        if a is None or b is None or a != b or a[1:] != (0, 0):
            raise ValueError('incompatible root tile')
    result = copy.deepcopy(table)
    for row in result:
        for pin in row['pins']:
            old = old_place[pin['block']]
            new = new_place[pin['block']]
            if (pin['x'], pin['y'], pin['layer']) != (old[0], old[1], old[3]):
                raise ValueError('source coordinate mismatch')
            tile = types[grid[(old[0], old[1], old[3])][0]]
            role = 'OUTPUT' if pin['index'] == 0 else 'INPUT'
            matches = [v for k, v in tile['pins'].items()
                       if k[1:] == (old[2], pin['port'], pin['bit'])]
            if matches != [(pin['class'], role, pin['physical_pin'])]:
                raise ValueError('physical pin/class mismatch')
            kind = 'SOURCE' if pin['index'] == 0 else 'SINK'
            if (new[0], new[1], new[3], pin['class'], kind) not in endpoints:
                raise ValueError('destination RR class absent')
            pin.update(x=new[0], y=new[1], layer=new[3])
    return result
