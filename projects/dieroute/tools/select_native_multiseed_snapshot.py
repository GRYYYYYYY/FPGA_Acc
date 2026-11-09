"""Select the first chronological proposal whose root/sink masks are disjoint."""
import json
import mmap
import struct
import sys
from pathlib import Path

def select(route):
    with (route/'net_commit_frames.bin').open('rb') as ff, (route/'net_commit_policy.bin').open('rb') as pf, mmap.mmap(ff.fileno(),0,access=mmap.ACCESS_READ) as frames, mmap.mmap(pf.fileno(),0,access=mmap.ACCESS_READ) as policy:
        position, previous, checked = 64, None, 0
        while position < len(frames):
            h = struct.unpack_from('<16Q',frames,position)
            cmd = struct.unpack_from('<16Q',frames,position+192)
            branches = position+448+h[8]*16+h[9]*64
            if h[6] == 3 and h[10]:
                checked += 1
                assert previous is not None
                ph, pp = previous
                nets = pp+448+ph[8]*16+ph[9]*64+ph[10]*64+ph[11]*16+ph[12]*64+(ph[13]+ph[14])*72
                net = None
                for i in range(ph[15]):
                    row = struct.unpack_from('<9Q',frames,nets+i*72)
                    if row[0] == cmd[3]:
                        net = row[1:]
                        break
                assert net is not None and net[1] == cmd[4]
                sink = struct.unpack_from('<Q',frames,branches+8)[0]
                source = net[2]
                a = (struct.unpack_from('<Q',policy,64+source*8)[0]>>32)&255
                b = (struct.unpack_from('<Q',policy,64+sink*8)[0]>>32)&255
                if a and b and not (a&b) and net[4]>1:
                    return dict(selection='First chronological cross-die proposal with multiple current-net tree seeds', sequence=h[0], source=source, sink=sink, source_mask=a, sink_mask=b, net=cmd[4], proposals_checked=checked,tree_seed_count=net[4])
            previous = h, position
            position += h[7]*8
        raise RuntimeError('no cross-die proposal')

if __name__ == '__main__':
    result = select(Path(sys.argv[1]))
    text = json.dumps(result,indent=2)+'\n'
    if len(sys.argv) == 3:
        Path(sys.argv[2]).write_text(text)
    print(text,end='')
