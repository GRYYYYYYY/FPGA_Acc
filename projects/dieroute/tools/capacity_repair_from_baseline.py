"""Repair capacity-invalid whole-net allocations using a legal frozen baseline.

This is a sufficient restoration rule, not a minimum restoration solver. Native
edge legality, timing and wirelength still require separate validation. The
existing capacity_restore_closure helper's stricter contract is unchanged.
"""
from collections import Counter, defaultdict
from numbers import Integral


def repair_capacity(baseline, candidate, capacities):
    """Return restored net IDs and wave counts; count each net once per node.

    Both allocations must contain the same complete set of nets. Include roots
    in each allocation. Only the baseline must already satisfy capacity. Every
    conflicting node causes all its current owners to revert to their baseline
    trees, including conflicts introduced by an earlier wave of restoration.

    Restorations are monotone. A conflict must have an unrestored owner because
    the baseline alone is legal; therefore at most len(baseline) waves add nets.
    An already legal candidate is returned unchanged. Inputs are never mutated.
    """
    if baseline.keys() != candidate.keys():
        raise ValueError('Baseline and candidate must contain identical net IDs')
    baseline = {net: frozenset(nodes) for net, nodes in baseline.items()}
    candidate = {net: frozenset(nodes) for net, nodes in candidate.items()}
    for allocation in (baseline, candidate):
        for nodes in allocation.values():
            for node in nodes:
                capacity = capacities.get(node)
                if not isinstance(capacity, Integral) or capacity < 0:
                    raise ValueError('Missing, negative or noninteger capacity')
    occupancy = Counter(node for nodes in baseline.values() for node in nodes)
    if any(count > capacities[node] for node, count in occupancy.items()):
        raise ValueError('Frozen baseline exceeds capacity')
    restored, waves = set(), []
    while True:
        owners = defaultdict(set)
        for net in baseline:
            for node in baseline[net] if net in restored else candidate[net]:
                owners[node].add(net)
        conflicts = [nets for node, nets in owners.items()
                     if len(nets) > capacities[node]]
        waves.append({'restored_nets': len(restored),
                      'overused_resources': len(conflicts)})
        if not conflicts:
            return restored, waves
        added = set().union(*conflicts) - restored
        if not added:
            raise RuntimeError('Legal baseline restoration cannot advance')
        restored.update(added)


def main():
    """Write a private candidate tree; native validation remains a separate step."""
    import argparse
    import csv
    import hashlib
    import json
    import mmap
    import struct
    from pathlib import Path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('resources', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.report.exists():
        parser.error('Output and report must be new paths')
    fields = ['net_id', 'source', 'parent', 'child']

    def load(path):
        trees, roots = defaultdict(dict), {}
        with path.open() as stream:
            for row in csv.DictReader(stream):
                net, source, parent, child = (int(row[k]) for k in fields)
                if min(net, source, parent, child) < 0:
                    raise ValueError('Negative tree identifier')
                if roots.setdefault(net, source) != source or child == source:
                    raise ValueError('Inconsistent root')
                if child in trees[net]:
                    raise ValueError('Repeated child')
                trees[net][child] = parent
        if not trees:
            raise ValueError('Empty tree collection')
        for net, parents in trees.items():
            reached = {roots[net]}
            for child in parents:
                chain, node = set(), child
                while node not in reached:
                    if node in chain or node not in parents:
                        raise ValueError('Cycle or disconnected tree')
                    chain.add(node)
                    node = parents[node]
                reached.update(chain)
        return dict(trees), roots

    baseline, roots = load(args.baseline)
    candidate, candidate_roots = load(args.candidate)
    if roots != candidate_roots:
        raise ValueError('Baseline and candidate roots differ')

    def allocation(trees):
        return {net: set(parents) | set(parents.values()) | {roots[net]}
                for net, parents in trees.items()}

    ba, ca = allocation(baseline), allocation(candidate)
    used = set().union(*ba.values(), *ca.values())
    with args.resources.open('rb') as stream:
        size = args.resources.stat().st_size
        if not size or size % 16 or max(used) >= size // 16:
            raise ValueError('Invalid resource extent or tree node outside resources')
        with mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
            capacities = {node: struct.unpack_from('<H', data, node * 16 + 2)[0]
                          for node in used}
    restored, waves = repair_capacity(ba, ca, capacities)
    with args.output.open('x', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow(fields)
        for net in sorted(baseline):
            parents = baseline[net] if net in restored else candidate[net]
            for child, parent in sorted(parents.items()):
                writer.writerow([net, roots[net], parent, child])
    files = [args.baseline, args.candidate, args.resources, args.output,
             Path(__file__).resolve()]
    report = {
        'status': 'capacity_repaired_tree_requires_native_legality_and_quality_validation',
        'total_nets': len(baseline), 'restored_nets': sorted(restored),
        'retained_candidate_nets': len(baseline) - len(restored), 'waves': waves,
        'source_sha256': {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in files},
        'scope': 'Whole trees restored without additional router iterations. '
                 'Native edge/sink-pin legality, CPD, wirelength and physical SLL '
                 'remain separate requirements. Original failed results retained.',
        'research_complete': False,
    }
    with args.report.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
