#!/usr/bin/env python3
"""Do not let timestamp normalization hide netlist or constraint changes."""
import importlib.util
from pathlib import Path
import tempfile
import zipfile

tool = Path(__file__).resolve().parents[1]/'tools/compare_checkpoint_members.py'
import sys
sys.path.insert(0, str(tool.parent))
spec = importlib.util.spec_from_file_location('checkpoint_members', tool)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    def fixture(name, timestamp='2026 10 13 1 2 3', net='signal', xdc='set_false_path -from clk', omit=False):
        path = root/(name+'.dcp')
        with zipfile.ZipFile(path, 'w') as z:
            z.writestr('top.edf', '(edif top\n (edifVersion 2 0 0)\n (edifLevel 0)\n (keywordMap (keywordLevel 0))\n (status\n (written\n  (timeStamp '+timestamp+')\n ))\n (net '+net+'))\n')
            if not omit:
                z.writestr('top.xdc', xdc)
            z.writestr('top.xdef', 'physical changes are outside this comparator')
        return path
    base = module.inspect(fixture('base'))
    stamp = module.inspect(fixture('timestamp', timestamp='2026 10 14 2 3 4'))
    assert base['raw'] != stamp['raw'] and base['normalized'] == stamp['normalized']
    for name, kwargs in [('net', dict(net='other_signal')), ('constraint', dict(xdc='set_max_delay 2.0')), ('missing', dict(omit=True))]:
        assert module.inspect(fixture(name, **kwargs))['normalized'] != base['normalized'], name
    try:
        module.inspect(fixture('malformed', timestamp='NORMALIZED'))
    except ValueError:
        pass
    else:
        raise AssertionError('malformed timestamp accepted')
print('timestamp equivalence, net/constraint/member changes and malformed header checks passed')
