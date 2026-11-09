"""Independent lowered-interface and sequential obligation audit after terminal synthesis."""
import json,hashlib
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'briey_lowered_synthesis_v1_2026-10-09';D=E/'briey_lowered_synthesis_verification_v1_2026-10-09'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=json.loads((B/'receipt.json').read_text());assert r['exit_code']==0
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
before=json.loads((B/'input.json').read_text())['modules']['Briey'];after=json.loads((B/'design.json').read_text())['modules']['Briey'];assert set(after['ports'])==set(before['ports'])
for name,p in before['ports'].items():
 q=after['ports'][name];assert q['direction']==p['direction'] and len(q['bits'])==len(p['bits']);assert q['direction']!='inout'
def initialized(m):return {n:(len(v['bits']),v['attributes']['init']) for n,v in m['netnames'].items() if 'init' in v.get('attributes',{})}
assert initialized(after)==initialized(before)
neg=[c for c in after['cells'].values() if c['type']=='$_DFF_N_'];assert len(neg)==1
clock=after['ports']['io_jtag_tck']['bits'];assert neg[0]['connections']['C']==clock
q=neg[0]['connections']['Q'][0];assert any(q in v['bits'] and 'jtag_tap_tdoUnbufferd_regNext' in n for n,v in after['netnames'].items())
drivers={}
for c in after['cells'].values():
 if c['type'].startswith('$_DFF'):
  bit=c['connections']['Q'][0];assert bit not in drivers;drivers[bit]=c
initial=[]
for n,v in after['netnames'].items():
 if 'init' not in v.get('attributes',{}):continue
 for bit,state in zip(v['bits'],v['attributes']['init'][::-1]):
  if state=='x':continue
  assert bit in drivers and state in '01';initial.append(dict(net=n,q_bit=bit,value=state,ff_type=drivers[bit]['type']))
assert len(initial)==6 and all(x['value']=='0' for x in initial)
D.mkdir(exist_ok=False);report=dict(bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'receipt.json',B/'input.json',B/'design.json')},port_count=len(after['ports']),ports_name_direction_width_preserved=True,negative_ff_clock_and_q_named_identity=True,initialized_bits=initial,cell_types=dict(Counter(c['type'] for c in after['cells'].values())),scope='Lowered port shape, named negative FF clock/Q, defined-init net/FF-Q obligations only; no complete sequential or pad wrapper four-state equivalence, route labels or timing proof.')
(D/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS lowered interface, negative clock and six initialized FF bits')
