"""Check native fanout-base-cost scaling applicability on frozen development architectures."""
import json,hashlib
from decimal import Decimal
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1]
source=root/'work/vpr_source_bound_timing_build_20261015/source_vtr/vpr/src/route/route_net.cpp'
callsite=source.with_suffix('.tpp');text=source.read_text()
assert 'factor = sqrt(fanout);' in text and '.T_quadratic > 0.' in text
assert 'saved_base_cost * factor' in text and 'update_rr_base_costs(num_sinks);' in callsite.read_text()
files=[source,callsite,Path(__file__).resolve()];cases={}
for case in ['ex5p','diffeq','alu4']:
    path=root/f'work/native_costs_{case}_20261013/rr_indexed_data.echo';files.append(path);rows=[]
    for line in path.read_text().splitlines()[2:]:
        fields=line.split()
        if not fields:continue
        channel=fields[1] in ('CHANX','CHANY');offset=3 if channel else 2
        assert len(fields)==offset+7
        if channel:
            quadratic=Decimal(fields[offset+5]);assert quadratic.is_finite() and quadratic>=0
            rows.append(dict(index=int(fields[0]),kind=fields[1],segment=fields[2],printed_T_quadratic=str(quadratic),fanout_scaling_branch_active=quadratic>0))
    assert rows and all(not r['fanout_scaling_branch_active'] for r in rows)
    cases[case]=rows
architecture=root/'work/native_ex5p_stratix2die_cw80_20261013/architecture.xml';files.append(architecture)
switches=[dict(name=s.attrib['name'],type=s.attrib['type']) for s in ET.parse(architecture).getroot().findall('./switchlist/switch')]
assert switches and all(s['type']=='mux' for s in switches)
report=dict(status='native_pass_transistor_fanout_scaling_inactive_in_all_three_printed_development_tables',cases=cases,architecture_switches=switches,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},conclusion='Do not introduce unconditional sqrt(fanout) scaling as a supposed native-equivalence correction for these tables. Native code scales only positive T_quadratic rows;all observed channel rows print0.',scope='Source-condition plus frozen printed table evidence on3developmentinputs,not bit-exact internal float proof or explanation of CPD/WL regression. Other native objective differences including RC/fanout effects elsewhere remain open.',board_result=False,research_complete=False)
output=root/'work/vpr_fanout_scaling_applicability_20261015.json';output.write_text(json.dumps(report,indent=2)+'\n');print(report['status'])
