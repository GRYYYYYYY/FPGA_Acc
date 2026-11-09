"""Resolve init aliases and real control FF drivers after full gate lowering."""
import hashlib
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'full_native_ram_gate_controls_v1_2026-10-09'; D.mkdir(exist_ok=False)
source=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json'
gates=E/'full_native_ram_gates_v3_2026-10-09/gates.json'
receipt=gates.parent/'receipt.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads(receipt.read_text()); assert r['exit_code']==0
for p,h in {**r['bindings'],**r['files']}.items():assert sha(Path(p))==h
a=json.loads(source.read_text())['modules']['VexRiscvFull']
b=json.loads(gates.read_text())['modules']['VexRiscvFull']
assert a['ports']==b['ports']
bits=lambda name:b['netnames'][name]['bits']
initial={}
for name,net in b['netnames'].items():
    if 'init' not in net['attributes']:continue
    for bit,value in zip(net['bits'],reversed(net['attributes']['init'])):
        assert bit not in initial or initial[bit]==value
        initial[bit]=value
rows=[]
for name,net in a['netnames'].items():
    if 'init' not in net['attributes']:continue
    assert net['attributes']['init']=='0' and len(net['bits'])==1
    q=bits(name); assert len(q)==1 and initial[q[0]]=='0'
    drivers=[c for c in b['cells'].values() if c['type']=='$_DFF_P_' and c['connections']['Q']==q]
    assert len(drivers)==1
    prefix,control=name.rsplit('.',1); signal='we' if control=='pw' else 're'
    assert control in ['pw','er']
    c=drivers[0]['connections']
    assert c['D']==bits(prefix+'.'+signal) and c['C']==bits(prefix+'.clk')
    aliases=[n for n,v in b['netnames'].items() if v['bits']==q and v['attributes'].get('init')=='0']
    assert aliases
    rows.append(dict(name=name,bit=q[0],init_zero_aliases=aliases,positive_ff_driver=True))
assert len(rows)==30 and len({r['bit'] for r in rows})==13
macros={n:c for n,c in a['cells'].items() if c['type']=='dual_port_ram'}
assert len(macros)==15
for name,old in macros.items():
    new=b['cells'][name]
    for key in ['type','parameters','port_directions']:assert old[key]==new[key]
    prefix=name.rsplit('.',1)[0]
    pin_to_signal=dict(addr1='pa',addr2='ra',clk='clk',data1='pd',out1='unused',out2='raw',we1='pw')
    for pin,signal in pin_to_signal.items():assert new['connections'][pin]==bits(prefix+'.'+signal)
    assert new['connections']['we2']==['0'] and new['connections']['data2']==['0']*20
out=dict(passed=True,controls=rows,original_control_labels=30,distinct_initialized_control_bits=13,
    native_ram_instances_pin_readback=15,top_ports_exact=True,
    explanation='All 30 controls retained as aliases of 13 initialized positive-edge FFs; none became constant or lost zero initialization.',
    scope='Control and RAM pin structural audit. Not gate combinational equivalence, Full sequential equivalence or native packing.',
    bindings={str(p):sha(p) for p in [Path(__file__),source,gates,receipt]})
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n')
print(out['explanation'])
