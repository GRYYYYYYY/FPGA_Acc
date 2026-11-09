"""Independently compare raw snapshot exports with the first proposal's pre-state."""
import hashlib
import json
import mmap
import struct
import sys
from pathlib import Path

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()

def audit(source, out):
    meta = json.loads((out / 'snapshot.json').read_text())
    with source.open('rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as data:
        assert data[:8] == b'FPGAACCP'
        position = 64
        previous = None
        while position < len(data):
            h = struct.unpack_from('<16Q', data, position)
            cfg = struct.unpack_from('<8Q', data, position + 128)
            cmd = struct.unpack_from('<16Q', data, position + 192)
            ctl = struct.unpack_from('<8Q', data, position + 384)
            sections = position + 448
            branches = sections + h[8] * 16 + h[9] * 64
            indexed = branches + h[10] * 64 + h[11] * 16 + h[12] * 64
            assert indexed + (h[13] + h[14] + h[15]) * 72 == position + h[7] * 8
            if h[6] == 3 and h[0] == meta['proposal_sequence']:
                assert previous is not None and h[10]
                ph, pcfg, pctl, cursor = previous
                assert list(cfg) == meta['config'] and cfg == pcfg
                assert ph[0] == meta['source_frame_sequence'] and h[0] == meta['proposal_sequence']
                assert (pctl[0], pctl[1]) == (cmd[0], cmd[2]) == (meta['session'], meta['revision'])
                assert cmd[3:5] == (meta['net_slot'], meta['net_id'])
                assert struct.unpack_from('<Q', data, branches + 8)[0] == meta['sink']
                for name, count, capacity in zip(('resources', 'trees', 'nets'), ph[13:16], (cfg[2]*cfg[3], cfg[5], cfg[4])):
                    expected = {}
                    for _ in range(count):
                        row = struct.unpack_from('<9Q', data, cursor)
                        assert row[0] not in expected and row[0] < capacity
                        expected[row[0]] = row[1:]
                        cursor += 72
                    raw = (out / (name + '.raw')).read_bytes()
                    assert len(raw) == capacity * 64
                    for index, row in enumerate(struct.iter_unpack('<8Q', raw)):
                        assert row == expected.get(index, (0,)*8), (name, index)
                assert (out/'control.raw').read_bytes() == struct.pack('<8Q', *pctl)
                trees = (out/'trees.raw').read_bytes()
                nets = (out/'nets.raw').read_bytes()
                net = struct.unpack_from('<8Q', nets, cmd[3]*64)
                assert net[:2] == (cmd[0], cmd[4]) and net[5] == cmd[5]
                seeds = []
                index = net[3]
                for _ in range(net[4]):
                    assert index < pctl[3]
                    tree = struct.unpack_from('<8Q', trees, index*64)
                    assert tree[0] == cmd[0] and tree[2] == cmd[3]
                    seeds.append(tree)
                    index = tree[6]
                assert index == (1 << 64)-1 and len(seeds) == meta['seed_count']
                assert (out/'tree_seeds.raw').read_bytes() == b''.join(struct.pack('<8Q', *r) for r in seeds)
                break
            previous = h, cfg, ctl, indexed
            position += h[7]*8
        else:
            raise AssertionError('no proposal')
    files = [source, *sorted(out.glob('*.raw')), out/'snapshot.json', Path('tools/export_native_search_snapshot.cpp')]
    result = dict(status='passed', source_sha256=digest(source), hashes={str(p): digest(p) for p in files[1:]},
                  selection=meta['selection'], seeds=meta['seed_count'],
                  scope='Exact pre-proposal authority and complete tree seeds; not a search result or concurrency proof', board_result=False)
    (out/'independent_audit.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(status='passed', seeds=meta['seed_count'])))

if __name__ == '__main__':
    audit(Path(sys.argv[1]), Path(sys.argv[2]))
