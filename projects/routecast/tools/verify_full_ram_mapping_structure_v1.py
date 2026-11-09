"""Independent concrete wrapper and native-pin readback audit."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'full_ram_mapping_candidate_v1_2026-10-09'
receipt=json.loads((D/'receipt.json').read_text())
assert receipt['exit_code']==0
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
original=json.loads((E/'vexriscv_full_memory_candidate_v2_2026-10-09/design.json').read_text())['modules']['VexRiscvFull']
candidate=json.loads((D/'candidate.json').read_text())['modules']['VexRiscvFull']
out=json.loads((D/'structural.json').read_text())['modules']['VexRiscvFull']
plan=json.loads((E/'full_ram_lane_plan_v1_2026-10-09/plan.json').read_text())
assert candidate['ports']==original['ports']==out['ports']
for n,c in original['cells'].items():
    if c['type']!='$mem_v2':assert candidate['cells'][n]==c
assert set(candidate['cells'])==set(original['cells'])
net=lambda n:out['netnames'][n]['bits']
count=0
for row in plan['memories']:
    for j,s in enumerate(row['slices']):
        prefix=f"{row['name']}.s{j}"
        macro=out['cells'][prefix+'.ram']; c=macro['connections']
        assert macro['type']=='dual_port_ram'
        assert int(macro['parameters']['ADDR_WIDTH'],2)==10
        assert int(macro['parameters']['DATA_WIDTH'],2)==20
        assert c['clk']==[s['clock']] and c['we2']==['0'] and c['data2']==['0']*20
        assert c['addr2']==s['read_addr']
        for pin,signal in [('we1','pw'),('addr1','pa'),('data1','pd'),('out2','raw')]:
            assert c[pin]==net(prefix+'.'+signal)
        for control in ['pw','er']:
            assert out['netnames'][prefix+'.'+control]['attributes']['init']=='0'
        # Verify the actual sequential drivers, including CE selection and pending write.
        for qname,expected in [('pw',[s['write_enable']]),('er',[s['read_enable']]),
                               ('pa',s['write_addr']),('pd',s['write_data'])]:
            q=net(prefix+'.'+qname)
            drivers=[v for v in out['cells'].values() if v['type']=='$dff' and v['connections']['Q']==q]
            assert len(drivers)==1
            drv=drivers[0]
            assert drv['connections']['D']==expected and drv['connections']['CLK']==[s['clock']]
            assert int(drv['parameters']['CLK_POLARITY'],2)==1
        count+=1
report=dict(passed=True,native_macros=count,untouched_nonmemory_cells=True,
    top_ports_exact=True,pending_write_and_read_enable_init_zero=True,
    scope='Blackbox structural pin and sequential driver readback only. Collision behavior, complete output compensation equivalence and native packing remain unverified.',
    bindings={str(p):sha(p) for p in [Path(__file__),D/'structural.json',D/'candidate.json',D/'wrappers.v']})
(D/'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
