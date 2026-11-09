#!/usr/bin/env python3
"""Check that raw CSR protection metadata preserves every provisional candidate's original footprint."""
import argparse
from contextlib import ExitStack
import json
import mmap
from pathlib import Path
import shutil
import struct
from run_native_case import sha256


def main():
    if not __debug__:
        raise RuntimeError("audit assertions require Python without optimization")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csr-run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / Path(__file__).name)
    shutil.copyfile(Path(__file__).with_name("run_native_case.py"), out / "run_native_case.py")
    run = args.csr_run.resolve()
    rm = json.loads((run / "manifest.json").read_text())
    assert rm["schema"] == "dieroute.native_csr_run.v1" and rm["status"] == "passed" and rm["inputs_unchanged"]
    step = rm["steps"][1]
    assert step["name"] == "verify" and step["returncode"] == 0
    mapping, footprint, csr = map(Path, step["command"][2:5])
    fm = json.loads((footprint.parent / "manifest.json").read_text())
    assert sha256(footprint.parent / "manifest.json") == rm["parent_manifests"][str(footprint.parent / "manifest.json")]
    paths = {"nets": footprint / "nets.bin", "pins": footprint / "pins.bin", "pips": footprint / "pips.bin",
             "node_map": mapping / "footprint_node_map.bin", "protection": csr / "protection.bin"}
    hashes = {k: sha256(p) for k, p in paths.items()}
    for key in ("nets", "pins", "pips"):
        assert hashes[key] == fm["artifacts"]["footprint/" + key + ".bin"]
    assert hashes["node_map"] == rm["inputs"][str(paths["node_map"])]
    assert hashes["protection"] == rm["artifacts"]["csr/protection.bin"]
    candidate_pins = candidate_pips = protected_pins = protected_pips = 0
    with ExitStack() as stack:
        data = {}
        for k, path in paths.items():
            stream = stack.enter_context(path.open("rb"))
            data[k] = stack.enter_context(mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ))
        n = data["nets"]
        node_map, mask = data["node_map"], data["protection"]
        assert mask[:8] == b"FPGAACCP" and struct.unpack_from("<I", mask, 12)[0] == 0x44520003

        def protection(node):
            device_id = struct.unpack_from("<I", node_map, node * 4)[0]
            return mask[64 + device_id]

        for net, node, _, _ in struct.iter_unpack("<4I", data["pins"]):
            if struct.unpack_from("<I", n, net * 64)[0] == 0:
                candidate_pins += 1
                protected_pins += protection(node) != 0
        for net, source, sink, _, _, _, _, flags in struct.iter_unpack("<8I", data["pips"]):
            if struct.unpack_from("<I", n, net * 64)[0] == 0:
                candidate_pips += 1
                assert not flags & (4 | 8 | 16 | 32), "candidate retains fixed/route-through/stub PIP"
                protected_pips += protection(source) != 0 or protection(sink) != 0
    assert protected_pins == protected_pips == 0, "candidate original route conflicts with immutable-resource metadata"
    report = {"schema": "dieroute.candidate_protection_audit.v1", "passed": True,
              "csr_manifest": str(run / "manifest.json"), "csr_manifest_sha256": sha256(run / "manifest.json"),
              "inputs": {str(paths[k]): h for k, h in hashes.items()},
              "candidate_pins_checked": candidate_pins, "candidate_pips_checked": candidate_pips,
              "candidate_pins_on_protected_nodes": protected_pins, "candidate_pips_touching_protected_nodes": protected_pips,
              "scope": "metadata does not block original candidate pin/PIP footprints; no new routing or controller protection proof"}
    (out / "audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": True, "candidate_pins": candidate_pins, "candidate_pips": candidate_pips}))


if __name__ == "__main__":
    main()
