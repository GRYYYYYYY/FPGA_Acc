"""Recompute exact lane coverage independently from the collected input."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
D=R/'experiments/full_ram_lane_plan_v1_2026-10-09'
p=json.loads((D/'plan.json').read_text())
source=Path(p['source'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==p['source_sha256']
cells=json.loads(source.read_text())['modules']['VexRiscvFull']['cells']
assert {r['name'] for r in p['memories']}=={n for n,c in cells.items() if c['type']=='$mem_v2'}
covered=0
for r in p['memories']:
    c=cells[r['name']]['connections']; w=r['width']
    for rd in range(r['read_ports']):
        ss=[s for s in r['slices'] if s['read_port']==rd]
        lanes=[i for s in ss for i in range(s['start'],s['stop'])]
        assert lanes==list(range(w))
        for s in ss:
            a,b=s['start'],s['stop']; count=b-a
            assert s['write_data'][:count]==c['WR_DATA'][a:b]
            assert s['logical_read_data']==c['RD_DATA'][rd*w+a:rd*w+b]
            assert s['write_data'][count:]==['0']*(20-count)
            ab=len(c['WR_ADDR'])
            assert s['write_addr']==c['WR_ADDR']+['0']*(10-ab)
            assert s['read_addr']==c['RD_ADDR'][rd*ab:(rd+1)*ab]+['0']*(10-ab)
            assert s['read_enable']==c['RD_EN'][rd]
            assert s['write_enable']==c['WR_EN'][a] and len(set(c['WR_EN'][a:b]))==1
            assert s['clock']==c['WR_CLK'][0]==c['RD_CLK'][rd]
            covered+=count
out=dict(passed=True,memories=len(p['memories']),covered_read_data_lanes=covered,
    plan_sha256=hashlib.sha256((D/'plan.json').read_bytes()).hexdigest(),
    scope='Exact slice/replica wire coverage only; no RTL or native functional admission.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
