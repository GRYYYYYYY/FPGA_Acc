#!/usr/bin/env python3
"""Hand oracle for direction, parallel identity, CRC and background metadata."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

FINGERPRINT = "0123456789abcdef0123456789abcdef"


def crc(data):
    value = 0
    for b in data:
        value ^= b << 56
        for _ in range(8):
            value = ((value << 1) ^ (0x42f0e1eba9ea3693 if value >> 63 else 0)) & ((1 << 64) - 1)
    return value


def table(path, rows):
    path.write_bytes(b"".join(struct.pack("<" + "I" * len(r), *r) for r in rows))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("builder", "verifier"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.output is None:
        scratch = tempfile.TemporaryDirectory(prefix="dieroute_native_csr_")
        args.output = Path(scratch.name) / "fixture"
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    for d in ("graph", "mapped", "footprint"):
        (out / d).mkdir()
    assert crc(b"123456789") == 0x6c40df5f0b497347
    nodes = [[i, 0, i, 0, i, mask, 1, 0, flag, 0, 0, 0, 0, 0, 0, 0]
             for i, (mask, flag) in enumerate([(1, 0), (3, 0), (2, 0), (1, 1), (1, 4), (2, 0)])]
    table(out / "graph/nodes.bin", nodes)
    pips = [[0, 0, 1, 0, 10, 11, 0, 0], [1, 2, 1, 1, 12, 11, 1, 2],
            [2, 0, 1, 0, 20, 21, 0, 0], [3, 1, 3, 0, 11, 13, 0, 8],
            [4, 0xffffffff, 0, 0, 0, 10, 0, 0], [5, 5, 2, 1, 15, 12, 1, 1],
            [6, 3, 3, 0, 13, 23, 0, 2]]
    table(out / "graph/pips.bin", pips)
    table(out / "mapped/occupied_nodes.bin", [[0, 0, 17, 1, 0, 1, 0, 0], [1, 1, 17, 1, 0, 1, 0, 0],
                                               [2, 2, 17, 1, 0, 1, 4, 0], [3, 3, 18, 1, 1, 0, 1, 0]])
    table(out / "mapped/footprint_node_map.bin", [[i] for i in range(6)])
    table(out / "mapped/footprint_pip_map.bin", [[0], [1], [5]])
    table(out / "footprint/pips.bin", [[17, 0, 1, 0, 10, 11, 0, 0], [17, 2, 1, 1, 12, 11, 1, 3], [17, 5, 2, 1, 15, 12, 1, 1]])

    def run(cmd, log):
        result = subprocess.run(cmd, capture_output=True, text=True)
        (out / log).write_text(result.stdout + result.stderr)
        return result

    build = [str(args.builder.resolve()), str(out / "graph"), str(out / "mapped"), FINGERPRINT, str(out / "csr")]
    result = run(build, "build.log")
    assert result.returncode == 0, result.stderr
    expected = {"offsets.bin": struct.pack("<7Q", 0, 2, 4, 6, 8, 8, 8),
                "arcs.bin": b"".join(struct.pack("<II", *r) for r in [(1, 0), (1, 4), (2, 3), (3, 6), (1, 2), (5, 11), (3, 12), (3, 13)]),
                "protection.bin": bytes([0, 0, 2, 5, 8, 0])}
    for name, payload in expected.items():
        data = (out / "csr" / name).read_bytes()
        assert data[:8] == b"FPGAACCP" and data[64:] == payload
        assert struct.unpack_from("<Q", data, 48)[0] == crc(payload)

    cases = [("base", None, None, None, None, False)] + [
        ("crc_corruption", "arcs.bin", 64, bytes([7]), "container CRC64", False),
        ("fingerprint_corruption", "arcs.bin", 32, bytes([255]), "architecture fingerprint", False),
        ("wrong_object_type", "arcs.bin", 12, struct.pack("<I", 0), "container type/flags", False),
        ("wrong_schema", "arcs.bin", 10, bytes([2]), "container schema", False),
        ("wrong_payload_size", "arcs.bin", 24, struct.pack("<Q", 0), "container payload length", False),
        ("illegal_direction", "arcs.bin", 68, struct.pack("<I", 1), "illegal PIP direction", True),
        ("wrong_bidirectional_orientation", "arcs.bin", 84, struct.pack("<I", 2), "arc endpoint/PIP identity", True),
        ("duplicate_parallel_identity", "arcs.bin", 76, struct.pack("<I", 0), "arc order or duplicate", True),
        ("missing_background_mark", "protection.bin", 67, bytes([4]), "immutable resource metadata mismatch", True),
        ("offset_regression", "offsets.bin", 80, struct.pack("<Q", 1), "CSR offset monotonicity", True),
    ]
    results = []
    for name, filename, offset, value, error, repair_crc in cases:
        directory = out / "csr"
        if filename:
            directory = out / name
            shutil.copytree(out / "csr", directory)
            data = bytearray((directory / filename).read_bytes())
            data[offset:offset + len(value)] = value
            if repair_crc:
                struct.pack_into("<Q", data, 48, crc(data[64:]))
            (directory / filename).write_bytes(data)
        cmd = [str(args.verifier.resolve()), str(out / "graph"), str(out / "mapped"), str(out / "footprint"), str(directory), FINGERPRINT, str(out / (name + "_audit"))]
        result = run(cmd, name + ".log")
        if error:
            assert result.returncode != 0 and error in result.stderr, (name, result.stderr)
        else:
            assert result.returncode == 0, result.stderr
            audit = json.loads((out / "base_audit/audit.json").read_text())
            assert audit["arcs"] == 8 and audit["original_DCP_PIPs_direction_matched"] == 3
            assert audit["parallel_destination_groups"] == audit["parallel_extra_arcs"] == 2
            assert audit["original_reversed_PIPs"] == audit["self_arcs"] == 2
        results.append({"case": name, "passed": True, "returncode": result.returncode})
    (out / "tests.json").write_text(json.dumps({"passed": True, "cases": results, "crc64_known_vector_passed": True}, indent=2) + "\n")
    print(json.dumps({"passed": True, "cases": len(results)}))


if __name__ == "__main__":
    main()
