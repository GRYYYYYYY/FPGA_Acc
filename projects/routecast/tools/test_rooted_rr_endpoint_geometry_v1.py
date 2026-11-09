"""Regression for an internal hard-block endpoint and neighboring-tile rejection."""
import json
from pathlib import Path
from rooted_rr_endpoint_geometry_v1 import validate
from pre_route_endpoints import sha

position = (3, 5, 0, 0, 17)
grid = {(3, y, 0): (2, 0, y - 5) for y in range(5, 8)}
grid[3, 8, 0] = (2, 0, 0)
dimensions = {2: (1, 3)}
inside = dict(layer='0', xlow='3', xhigh='3', ylow='6', yhigh='7')
assert validate(inside, position, grid, dimensions) == 2
assert validate(dict(inside, ylow='5', yhigh='5'), position, grid, dimensions) == 2
bad = [
    ('cross_next_tile', dict(inside, yhigh='8'), position, grid),
    ('wrong_layer', dict(inside, layer='1'), position, grid),
    ('nonroot_placement', inside, (3, 6, 0, 0, 17), grid),
    ('grid_owner_mismatch', inside, position, {**grid, (3, 7, 0): (2, 0, 0)}),
    ('reversed_bbox', dict(inside, ylow='7', yhigh='6'), position, grid),
]
for name, loc, pos, cells in bad:
    try:
        validate(loc, pos, cells, dimensions)
    except AssertionError:
        pass
    else:
        raise AssertionError(name)
out = Path(__file__).resolve().parents[1] / 'experiments/rooted_endpoint_geometry_contract_v1_2026-10-13'
out.mkdir()
sources = [Path(__file__).resolve(), Path(__file__).with_name('rooted_rr_endpoint_geometry_v1.py').resolve()]
(out / 'verification.json').write_text(json.dumps(dict(bindings={str(p): sha(p) for p in sources}, valid_cases=2, rejected_cases=[x[0] for x in bad], all_pass=True), indent=2) + '\n')
print('ROOTED GEOMETRY PASS 2 valid, 5 rejected')
