"""Validate an endpoint bbox against its entire rooted physical tile footprint."""


def validate(loc, position, grid, dimensions):
    x, y, subtile, layer, block_id = position
    assert int(loc.get('layer', 0)) == layer
    tid, dx, dy = grid[x, y, layer]
    assert (dx, dy) == (0, 0)
    width, height = dimensions[tid]
    xl, xh, yl, yh = [int(loc[k]) for k in ['xlow', 'xhigh', 'ylow', 'yhigh']]
    assert x <= xl <= xh < x + width and y <= yl <= yh < y + height
    for xx in range(xl, xh + 1):
        for yy in range(yl, yh + 1):
            other, ox, oy = grid[xx, yy, layer]
            assert other == tid and (xx - ox, yy - oy) == (x, y)
    return tid
