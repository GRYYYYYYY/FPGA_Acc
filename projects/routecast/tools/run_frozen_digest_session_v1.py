"""Explicit runtime adapter; archived producer and shared sources stay unchanged."""
import json
import runpy
import sys
import time
from pathlib import Path
import pre_route_endpoints
from frozen_digest_session_v1 import FrozenDigestSession


def main():
    manifest, stats_file, script, *args = sys.argv[1:]
    original = pre_route_endpoints.sha
    session = FrozenDigestSession(json.loads(Path(manifest).read_text()), original)
    pre_route_endpoints.sha = session
    sys.argv = [script, *args]
    start = time.perf_counter()
    try:
        runpy.run_path(script, run_name='__main__')
    finally:
        pre_route_endpoints.sha = original
        with Path(stats_file).open('x') as f:
            json.dump(dict(stats=session.stats, process_body_seconds=time.perf_counter()-start,
                           adapter_sha256=original(__file__), manifest_sha256=original(manifest)),f,indent=2)
            f.write('\n')


if __name__ == '__main__':
    main()
