"""Replay exported path legality and negotiated cost against immutable authority."""
import json
import mmap
import struct
import sys
from pathlib import Path

art, snap, search = map(Path,sys.argv[1:4])
meta = json.loads((snap/'snapshot.json').read_text())
control = struct.unpack('<8Q',(snap/'control.raw').read_bytes())
seeds = {r[1]:r[5] for r in struct.iter_unpack('<8Q',(snap/'tree_seeds.raw').read_bytes())}
goal = struct.unpack('<8Q',(art/'goal.raw').read_bytes())
result = struct.unpack('<8Q',(art/'result.raw').read_bytes())
assert result[0] == 0
nodes = [r[0] for r in struct.iter_unpack('<I',(art/'path_nodes.raw').read_bytes())]
pips = [r[0] for r in struct.iter_unpack('<I',(art/'path_pips.raw').read_bytes())]
attachment, = struct.unpack('<Q',(art/'attachment.raw').read_bytes())
assert attachment in seeds and len(nodes)==len(pips)
assert (nodes[-1] if nodes else attachment) == meta['sink'] == goal[3]
assert goal[4] == seeds[attachment]+len(nodes)
authority = {}
for r in struct.iter_unpack('<8Q',(snap/'resources.raw').read_bytes()):
    if r[0] == control[0]:
        assert (r[4]&0xffffffff) not in authority
        authority[r[4]&0xffffffff] = r
observations = list(struct.iter_unpack('<8Q',(art/'observations.raw').read_bytes()))
assert len(observations) == result[5]
observed = set()
with Path(sys.argv[4]).open('rb') as pf,(search/'offsets.bin').open('rb') as of,(search/'arcs.bin').open('rb') as af, mmap.mmap(pf.fileno(),0,access=mmap.ACCESS_READ) as policy,mmap.mmap(of.fileno(),0,access=mmap.ACCESS_READ) as offsets,mmap.mmap(af.fileno(),0,access=mmap.ACCESS_READ) as arcs:
    for o in observations:
        node,version,occupancy,history,session,epoch,owner,reserved = o
        assert node < meta['config'][0] and session == control[0] and epoch == goal[0] and not reserved
        row = authority.get(node,(0,)*8)
        assert (version,occupancy,history) == (row[3],row[1],row[2])
        p, = struct.unpack_from('<Q',policy,64+node*8)
        mask = (p>>32)&255
        assert mask and owner == (mask&-mask).bit_length()-1
        observed.add(node)
    cost = 0
    parent = attachment
    for node,pip in zip(nodes,pips):
        assert node in observed and node not in seeds
        p, = struct.unpack_from('<Q',policy,64+node*8)
        assert not p&(1<<40) and p&0xffffffff in (0xffffffff,meta['net_id'])
        lo,hi = struct.unpack_from('<2Q',offsets,64+parent*8)
        end = hi
        while lo<hi:
            mid=(lo+hi)//2
            dst,edge=struct.unpack_from('<2I',arcs,64+mid*8)
            if (dst,edge)<(node,pip):lo=mid+1
            else:hi=mid
        assert lo<end and struct.unpack_from('<2I',arcs,64+lo*8)==(node,pip)
        row=authority.get(node,(0,)*8)
        cost += 1+row[2]+control[2]*row[1]
        parent=node
assert cost == goal[1]
report=dict(status='passed',path_edges=len(nodes),cost=cost,observations=len(observations),
    scope='Independent exported path/PIP legality and exact authority observation/cost replay; not an optimality or whole-design proof',board_result=False)
(art/'path_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
