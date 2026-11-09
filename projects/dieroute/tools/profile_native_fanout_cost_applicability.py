"""Check applicability of the frozen VPR sqrt(fanout) base-cost branch."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = root/'work/vpr_source_bound_initial_observation_build_20261015/source_vtr/vpr/src/route/route_net.cpp'
text = source.read_text()
assert 'factor = sqrt(fanout);' in text
assert 'T_quadratic > 0.' in text
sources = {str(source):hashlib.sha256(source.read_bytes()).hexdigest(),
           str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
records = {}
for case in ['ex5p','diffeq','alu4']:
    path = root/f'work/native_costs_{case}_20261013/rr_indexed_data.echo'
    lines = path.read_text().splitlines()
    assert 'T. Quadratic' in lines[1]
    rows = []
    for line in lines[2:]:
        f = line.split()
        if not f: continue
        channel = f[1] in ['CHANX','CHANY']
        offset = 3 if channel else 2
        assert len(f) == offset+7
        value = Decimal(f[offset+5])
        assert value.is_finite() and value >= 0
        rows.append(dict(index=int(f[0]),kind=f[1],quadratic=str(value),scaled=channel and value>0))
    assert rows and sum(r['kind'] in ['CHANX','CHANY'] for r in rows)>0
    records[case] = dict(rows=rows,positive_channel_classes=sum(r['scaled'] for r in rows))
    sources[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
assert all(r['positive_channel_classes']==0 for r in records.values())
out = root/'work/native_fanout_cost_applicability_20261015'
out.mkdir(exist_ok=False)
(out/'audit.json').write_text(json.dumps(dict(status='archived_echo_has_no_positive_quadratic_channel_classes',
    cases=records,source_sha256=sources,
    conclusion='The archived development echo tables do not support adding unconditional sqrt(fanout) base-cost scaling: the frozen VPR branch applies only to positive T_quadratic channel classes, and all printed development classes are zero.',
    scope='Frozen source and archived printed echo tables only. Printed zero is not an independent full-precision runtime observation; does not establish complete cost equivalence or explain remaining QoR regressions.',
    board_result=False,research_complete=False),indent=2)+'\n')
print(json.dumps({k:v['positive_channel_classes'] for k,v in records.items()}))
