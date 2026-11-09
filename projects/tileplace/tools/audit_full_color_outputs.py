"""Compare complete HLS output frames, including packed diagnostic buffers."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re


def audit(package, expected_transactions, log_path=None):
    kernel = (package / "full_kernel.cpp").read_text()
    signature = kernel.split('extern "C" void full_color_top(', 1)[1].split('){', 1)[0]
    # Match declarations individually so const input pointers cannot enter the audit.
    widths = {}
    for declaration in signature.split(','):
        if 'const ' in declaration:
            continue
        match = re.search(r'std::uint(8|32|64)_t\*\s*(\w+)', declaration)
        if match:
            widths[match[2]] = int(match[1])
    log_source = log_path if log_path is not None else package / 'run.log'
    log = log_source.read_text()
    progress = [int(n) for n in re.findall(r'RTL Simulation : (\d+) /', log)]
    completed = max(progress, default=0)
    assert completed <= expected_transactions
    tv = package / 'full_project/u280/sim/tv'
    rows = []
    for port, bits in sorted(widths.items()):
        cpu = (tv / 'cdatafile' / f'c.full_color_top.autotvout_{port}_mem.dat').read_bytes()
        rtl = (tv / 'rtldatafile' / f'rtl.full_color_top.autotvout_{port}_mem.dat').read_bytes()
        assert cpu[-8:].hex() == '5a5aa5a50f0ff0f0', port
        assert (len(cpu) - 8) % expected_transactions == 0, port
        frame_bytes = (len(cpu) - 8) // expected_transactions
        assert frame_bytes >= 8 and (frame_bytes - 8) % (bits // 8) == 0, port
        assert len(rtl) >= completed * frame_bytes, (port, completed, len(rtl))
        for transaction in range(completed):
            start = transaction * frame_bytes
            cframe = cpu[start:start + frame_bytes]
            rframe = rtl[start:start + frame_bytes]
            assert cframe[:8] == rframe[:8], (port, transaction, 'frame header')
            values = lambda frame: [int.from_bytes(frame[i:i + bits // 8], 'big')
                                    for i in range(8, len(frame), bits // 8)]
            cv, rv = values(cframe), values(rframe)
            differences = [i for i, (c, r) in enumerate(zip(cv, rv)) if c != r]
            rows.append(dict(port=port, transaction=transaction, element_bits=bits,
                             elements=len(cv), transport_header=int.from_bytes(cframe[:8], 'big'),
                             mismatches=len(differences), first_difference=None if not differences
                             else dict(index=differences[0], cpu=cv[differences[0]], rtl=rv[differences[0]])))
    return dict(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                scope='complete logged transactions only; whole typed payloads, not transport-header element counts',
                completed_transactions=completed, expected_transactions=expected_transactions,
                progress_log=str(log_source.resolve()),
                kernel_sha256=hashlib.sha256((package / 'full_kernel.cpp').read_bytes()).hexdigest(),
                all_compared_outputs_equal=bool(rows) and all(row['mismatches'] == 0 for row in rows),
                full_expected_outputs_equal=completed == expected_transactions and bool(rows)
                and all(row['mismatches'] == 0 for row in rows), ports=rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('package', type=Path)
    parser.add_argument('--transactions', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--log', type=Path, help='Progress log for this attempt; defaults to package/run.log')
    args = parser.parse_args()
    result = audit(args.package, args.transactions, args.log)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(dict(completed=result['completed_transactions'], comparisons=len(result['ports']),
                          differences=[{key: row[key] for key in ('port', 'transaction', 'mismatches')}
                                       for row in result['ports'] if row['mismatches']])))
