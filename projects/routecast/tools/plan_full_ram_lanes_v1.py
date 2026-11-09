"""Concrete source-lane plan; deliberately not a native mapping admission."""
import hashlib
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
source = R / 'experiments/vexriscv_full_memory_candidate_v2_2026-10-09/design.json'
D = R / 'experiments/full_ram_lane_plan_v1_2026-10-09'
D.mkdir(exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
m = json.loads(source.read_text())['modules']['VexRiscvFull']
rows = []
for name, cell in m['cells'].items():
    if cell['type'] != '$mem_v2':
        continue
    p, c = cell['parameters'], cell['connections']
    val = lambda key: int(p[key], 2)
    w, size, ab, nr = (val(k) for k in ('WIDTH', 'SIZE', 'ABITS', 'RD_PORTS'))
    assert val('WR_PORTS') == 1 and size <= 1024 and ab <= 10
    assert len(set(c['WR_EN'])) == 1
    assert val('RD_TRANSPARENCY_MASK') == val('RD_COLLISION_X_MASK') == 0
    assert c['RD_CLK'] == c['WR_CLK'] * nr
    slices = []
    # One single-write, separate-read dual-port macro per read replica and width slice.
    for rd in range(nr):
        for start in range(0, w, 20):
            stop = min(start + 20, w)
            slices.append(dict(read_port=rd, start=start, stop=stop,
                mode='mem_1024x20_dp', write_addr=c['WR_ADDR'] + ['0'] * (10-ab),
                read_addr=c['RD_ADDR'][rd*ab:(rd+1)*ab] + ['0'] * (10-ab),
                write_data=c['WR_DATA'][start:stop] + ['0'] * (20-(stop-start)),
                logical_read_data=c['RD_DATA'][rd*w+start:rd*w+stop],
                unused_read_lanes=list(range(stop-start,20)),
                write_enable=c['WR_EN'][0], read_enable=c['RD_EN'][rd],
                clock=c['WR_CLK'][0]))
    rows.append(dict(name=name,width=w,size=size,read_ports=nr,slices=slices))
plan = dict(source=str(source),source_sha256=sha(source),script_sha256=sha(Path(__file__)),
    memories=rows,macro_count=sum(len(r['slices']) for r in rows),
    physical_capacity_bits=sum(len(r['slices'])*1024*20 for r in rows),
    logical_capacity_bits=sum(r['width']*r['size'] for r in rows),
    admitted_for_prediction=False,
    obligations=['Pending-write compensation and CE hold required on every slice.',
        'Initialize pending write enable and read selector to zero; preserve undefined data.',
        'Native macro collision model and full sequential equivalence remain unverified.',
        'Plan is port wiring coverage, not emitted RTL, packed resources or timing evidence.'])
(D/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(json.dumps({k:plan[k] for k in ('macro_count','physical_capacity_bits','logical_capacity_bits')}))
