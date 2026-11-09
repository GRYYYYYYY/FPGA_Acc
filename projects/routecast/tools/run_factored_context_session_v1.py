"""Explicit factored-context adapter; owned archived producer stays untouched."""
import json
import runpy
import sys
from pathlib import Path
from pre_route_endpoints import sha
import cached_multiplicative_occupancy_context_v1 as target
from factored_multiplicative_context_v1 import Context


def main():
    receipt, script, *args = sys.argv[1:]
    original = target.Context
    target.Context = Context
    sys.argv = [script, *args]
    try:
        runpy.run_path(script, run_name='__main__')
    finally:
        target.Context = original
        Path(receipt).write_text(json.dumps(dict(adapter_sha256=sha(__file__),
            context_sha256=sha(Path(__file__).with_name('factored_multiplicative_context_v1.py')),
            scope='Runtime factored-price adapter,not original binary identity.'),indent=2)+'\n')


if __name__ == '__main__':
    main()
