#!/usr/bin/env python3
"""Compare nonphysical DCP members; normalize only the EDIF header timestamp."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from run_native_case import sha256


def inspect(path):
    members, normalized = {}, {}
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(('.edf', '.xdc', '.hwdef', '.v', '.vhdl')):
                continue
            raw, semantic = hashlib.sha256(), hashlib.sha256()
            with archive.open(name) as stream:
                if name.endswith('.edf'):
                    prefix = [stream.readline() for _ in range(7)]
                    if not re.fullmatch(rb'  \(timeStamp \d{4} \d{1,2} \d{1,2} \d{1,2} \d{1,2} \d{1,2}\)\n', prefix[6]):
                        raise ValueError('unsupported EDIF header timestamp: '+name)
                    raw.update(b''.join(prefix))
                    semantic.update(b''.join(prefix[:6])+b'  (timeStamp NORMALIZED)\n')
                for data in iter(lambda: stream.read(8*1024*1024), b''):
                    raw.update(data)
                    semantic.update(data)
            members[name] = raw.hexdigest()
            normalized[name] = semantic.hexdigest()
    if not any(name.endswith('.edf') for name in members):
        raise ValueError('no embedded EDIF')
    return dict(raw=members, normalized=normalized)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('control', type=Path)
    p.add_argument('routed', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    paths = dict(control=a.control.resolve(), routed=a.routed.resolve())
    inputs = {str(path): sha256(path) for path in paths.values()}
    values = {label: inspect(path) for label, path in paths.items()}
    equal = values['control']['normalized'] == values['routed']['normalized']
    unchanged = all(sha256(path) == digest for path, digest in inputs.items())
    result = dict(schema='dieroute.checkpoint_members_comparison.v1', inputs=inputs, members=values,
                  inputs_unchanged=unchanged, equal_except_edif_header_timestamp=equal,
                  normalization='Only EDIF line 7 after exact timestamp syntax validation; every other byte retained',
                  scope='Embedded logical EDIF, all XDC members, HWDEF and HDL stubs; excludes physical XDEF and archive metadata',
                  source_sha256=sha256(__file__))
    with a.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(json.dumps(dict(equal_except_edif_header_timestamp=equal, inputs_unchanged=unchanged)))
    return 0 if equal and unchanged else 1


if __name__ == '__main__':
    raise SystemExit(main())
