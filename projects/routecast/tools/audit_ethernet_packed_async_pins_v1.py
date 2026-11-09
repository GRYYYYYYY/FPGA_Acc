"""Check primitive identity and connected reset/clock pins in completed packed XML."""
import json,sys,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/ethernet_projection_async_pack_v2_2026-10-08';rp=out/'receipt.json';r=json.loads(rp.read_text());assert r['exit_code']==0 and all(sha(k)==v for k,v in r['bindings'].items()) and all(sha(k)==v for k,v in r['files'].items());net=out/'design.net';assert net.is_file();root=E.parse(net).getroot();parents={c:p for p in root.iter() for c in p};expected={}
blif=R/'experiments/ethernet_hardware_projection_v1_2026-10-08/design.blif'
for line in blif.read_text().splitlines():
 t=line.split()
 if len(t)>1 and t[0]=='.subckt' and t[1] in ['$_DFF_PP0_','$_DFF_PP1_']:
  pins=dict(x.split('=',1) for x in t[2:]);assert set(pins)=={'C','D','R','Q'} and pins['Q'] not in expected;expected[pins['Q']]=dict(model=t[1],pins=pins)
observed={};types=Counter()
for block in root.iter('block'):
 if block.get('name')=='open' or list(block.findall('block')):continue
 parent=parents.get(block)
 if parent is None or parent.tag!='block' or parent.get('mode') not in ['reset_zero','reset_one']:continue
 assert block.get('instance')=='storage[0]';name=block.get('name');assert name in expected and name not in observed;mode=parent.get('mode');model='$_DFF_PP0_' if mode=='reset_zero' else '$_DFF_PP1_';assert expected[name]['model']==model
 inputs={p.get('name'):p.text.split() if p.text else [] for p in block.findall('inputs/port')};clocks={p.get('name'):p.text.split() if p.text else [] for p in block.findall('clocks/port')};outputs={p.get('name'):p.text.split() if p.text else [] for p in block.findall('outputs/port')}
 assert set(inputs)=={'D','R'} and set(clocks)=={'C'} and set(outputs)=={'Q'}
 assert all(len(values)==1 and values[0]!='open' for values in list(inputs.values())+list(clocks.values())+list(outputs.values()))
 observed[name]=dict(model=model,packed_inputs=inputs,packed_clocks=clocks,packed_outputs=outputs,original_pins=expected[name]['pins']);types[model]+=1
assert set(observed)==set(expected) and len(observed)==1239
bindings={str(p):sha(p) for p in [Path(__file__),rp,net,blif]};assert all(sha(k)==v for k,v in bindings.items())
(out/'async_pin_verification.json').write_text(json.dumps(dict(bindings=bindings,primitive_counts=types,all_asynchronous_primitive_names_modes_and_nonopen_D_R_C_Q_pins_pass=True,primitives=observed,scope='Packed atom identity and nonopen local pin wiring only. Does not independently resolve every hierarchical wire to original D/R/C signal, prove original HDL equivalence, or characterize reset recovery/removal timing. Not a native routing/heldout/netgain pass.'),indent=2)+'\n');print('PASS packed async pins',dict(types))
