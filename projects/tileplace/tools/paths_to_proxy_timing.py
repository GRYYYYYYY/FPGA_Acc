#!/usr/bin/env python3
"""Export proxy connection delays from packed graph and complete C-model paths."""
import argparse
import csv
import struct
from pathlib import Path

from tileplace_vpr import ContractError


def convert(prefix, paths_file, output):
    nodes = list(struct.iter_unpack('<IHH', Path(str(prefix) + '.nodes').read_bytes()))
    edges = list(struct.iter_unpack('<IHH', Path(str(prefix) + '.edges').read_bytes()))
    tasks = list(struct.iter_unpack('<IIIIHHIII', Path(str(prefix) + '.tasks').read_bytes()))
    task_ids = [t[0] for t in tasks]
    if not tasks or len(task_ids) != len(set(task_ids)):
        raise ContractError('empty or duplicate task set')
    paths = {}
    with paths_file.open(newline='') as source:
        for row in csv.DictReader(source):
            paths.setdefault(int(row['task_id']), []).append((int(row['path_index']), int(row['resource_id'])))
    if set(paths) != set(task_ids):
        raise ContractError('path task set differs from packed tasks')
    rows = []
    for task in tasks:
        sequence = sorted(paths[task[0]])
        if [index for index, _ in sequence] != list(range(len(sequence))):
            raise ContractError('path indexes must be unique and consecutive')
        current, delay = task[2], 0
        if len(sequence) > task[5]:
            raise ContractError('path exceeds task hop budget')
        for _, target in sequence:
            if not 0 <= current < len(nodes) or not 0 <= target < len(nodes):
                raise ContractError('path node outside graph')
            begin, count, _ = nodes[current]
            if begin + count > len(edges):
                raise ContractError('node adjacency outside edge array')
            choices = [e[2] for e in edges[begin:begin + count] if e[0] == target]
            if not choices:
                raise ContractError('path contains a non-edge')
            delay += min(choices)
            current = target
        if current != task[3]:
            raise ContractError('path does not reach task sink')
        rows.append([0, task[0], task[1], task[2], task[3], 1, delay, task[4]])
    # Validate the complete input before creating an output; never overwrite.
    with output.open('x', newline='') as target:
        writer = csv.writer(target)
        writer.writerow(['iteration', 'task_id', 'net_id', 'source', 'sink', 'routed', 'delay_ps', 'criticality_q'])
        writer.writerows(rows)
    return len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-prefix', type=Path, required=True)
    parser.add_argument('--paths', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print('Exported proxy delays:', convert(args.input_prefix, args.paths, args.output))


if __name__ == '__main__':
    main()
