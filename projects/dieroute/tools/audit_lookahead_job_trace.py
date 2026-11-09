"""Validate chronological estimator captures; incomplete/failed captures fail closed."""
import argparse
from array import array
import hashlib
import json
from pathlib import Path
import struct
import sys

MAGIC = 0x3152435452444944


def read_words(stream, count):
    assert count <= 134217728, 'unreasonable record allocation'
    data = stream.read(count * 8)
    assert len(data) == count * 8, 'truncated record'
    words = array('Q')
    words.frombytes(data)
    if sys.byteorder != 'little':
        words.byteswap()
    return words


def audit(path, index=None):
    assert sys.byteorder == 'little', 'snapshot hash encoding requires little endian'
    jobs = results = decisions = 0
    phases = {1: 0, 2: 0}
    n = edges = portals = 0
    active = None
    snapshot = None
    footer = False
    graph_hash = None
    with path.open('rb') as stream:
        assert struct.unpack('<Q', stream.read(8))[0] == MAGIC
        while True:
            header = stream.read(16)
            if not header:
                break
            assert len(header) == 16 and not footer
            tag, size = struct.unpack('<QQ', header)
            words = read_words(stream, size)
            if tag == 1:
                assert snapshot is None and len(words) >= 3
                n, edges, portals = words[:3]
                assert 0 < n <= 0xffffffff and edges <= 0xffffffff
                assert len(words) == 3 + 2*n + 2*edges + 6*portals
                for node in range(n):
                    row = words[3+2*node]
                    begin, count = row & 0xffffffff, row >> 32
                    assert begin <= edges and count <= edges-begin
                for edge in range(edges):
                    start = 3+2*n+2*edge
                    assert words[start] & 0xffffffff < n
                    assert words[start+1] >> 16 in (0, 1)
                snapshot = array('Q', [0]) * (4*n)
                graph_hash = hashlib.sha256(words.tobytes()).hexdigest()
            elif tag == 2:
                assert snapshot is not None and active is None and len(words) >= 5
                job, phase, metadata_count, changes, run_count = words[:5]
                assert job == jobs+1 and phase in phases
                assert len(words) == 5+metadata_count+5*changes+run_count
                metadata = words[5:5+metadata_count]
                assert len(metadata) >= 16
                stage, levels, seeds, banned, choices = metadata[10:15]
                assert 0 < stage < levels
                assert metadata_count == 16+levels+2*seeds+banned+3*choices
                assert metadata[2] < n and metadata[3] < n
                assert all(v in (0, 1) for v in metadata[7:10])
                previous_node = -1
                offset = 5+metadata_count
                for change in range(changes):
                    start = offset+5*change
                    node = words[start]
                    assert previous_node < node < n
                    previous_node = node
                    snapshot[4*node:4*node+4] = words[start+1:start+5]
                    assert snapshot[4*node+1] <= 0xffffffff
                if job == 1:
                    assert changes == n
                runs = words[offset+5*changes:]
                assert all((run >> 8) > 0 and (run & 255) < 16 for run in runs)
                assert sum(run >> 8 for run in runs) == n
                digest = hashlib.sha256(snapshot.tobytes()).hexdigest()
                active = (job, phase, levels, stage, digest)
                jobs += 1
                phases[phase] += 1
                if index:
                    index.write(json.dumps(dict(job=job, phase=phase, task=metadata[0], net=metadata[1],
                                                stage=stage, snapshot_sha256=digest))+'\n')
            elif tag == 3:
                assert active is not None and len(words) >= 7
                job, expanded, visits, cutoffs, labels, reads, extra = words[:7]
                assert job == active[0] and len(words) == 7+2*labels+reads+extra
                assert cutoffs in (0, 1)
                label_nodes = set()
                for i in range(labels):
                    key = words[7+2*i]
                    node, rank = key & 0xffffffff, key >> 32
                    assert node < n and key not in label_nodes
                    if active[1] == 2:
                        assert active[3] <= rank < active[2]
                    label_nodes.add(key)
                journal_nodes = set()
                for i in range(reads):
                    value = words[7+2*labels+i]
                    node, version = value & 0xffffffff, value >> 32
                    assert node < n and node not in journal_nodes
                    assert snapshot[4*node+1] == version
                    journal_nodes.add(node)
                if active[1] == 1:
                    assert extra == 0
                else:
                    suffix = words[7+2*labels+reads:]
                    assert len(suffix) >= 2 and extra == 2+2*suffix[1]
                    assert all(suffix[2+2*i] < n for i in range(suffix[1]))
                active = None
                results += 1
            elif tag == 4:
                assert active is None and len(words) == 9 and 0 < words[0] <= jobs
                assert words[2] <= 0xffffffff  # net identity
                decisions += 1
            elif tag == 6:
                assert len(words) == 2 and words[0] == jobs and words[1] == 0 and active is None
                footer = True
            else:
                raise AssertionError(f'unknown trace record {tag}')
    assert footer and jobs == results and jobs > 0
    return dict(status='chronological_full_snapshot_trace_integrity_verified', jobs=jobs, results=results,
                upstream_jobs=phases[1], reverse_jobs=phases[2], decisions=decisions,
                nodes=n, edges=edges, portals=portals, graph_payload_sha256=graph_hash,
                scope='Trace structural completeness, exact snapshot delta reconstruction and resource-version journals. '
                      'No independent estimator replay, quality, native parent equivalence or performance claim.',
                research_complete=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    with args.output.with_suffix('.index.jsonl').open('x') as index:
        result = audit(args.trace, index)
    h = hashlib.sha256()
    with args.trace.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    result['trace_sha256'] = h.hexdigest()
    result['source_sha256'] = {str(Path(__file__).resolve()): hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['status', 'jobs', 'upstream_jobs', 'reverse_jobs']}))


if __name__ == '__main__':
    main()
