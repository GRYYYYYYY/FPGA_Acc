"""Freeze explicit engineering development timing condition, distinct from product requirements."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_full_development_sdc_v1_2026-10-09';D.mkdir(exist_ok=False);p=E/'vexriscv_family_flattened_inventory_v1_2026-10-09/VexRiscvFull/design.json';m=json.loads(p.read_text())['modules']['VexRiscvFull'];assert m['ports']['clk']=={'direction':'input','bits':m['ports']['clk']['bits']} and len(m['ports']['clk']['bits'])==1
patterns={'input':[],'output':[]};expected={'input':set(),'output':set()}
for name,port in m['ports'].items():
 assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name)
 assert port['direction'] in patterns
 for i in range(len(port['bits'])):expected[port['direction']].add(name if len(port['bits'])==1 else name+'['+str(i)+']')
 if name!='clk':patterns[port['direction']].append(name+'*' if len(port['bits'])>1 else name)
allnames=expected['input']|expected['output'];matched={}
for direction,items in patterns.items():
 selected=set()
 for pattern in items:
  regex=pattern.replace('*','.*');hit={name for name in allnames if re.fullmatch(regex,name)};assert hit and hit<=expected[direction];selected|=hit
 assert selected==expected[direction]-{'clk'};matched[direction]=sorted(selected)
sdc='''# Development engineering condition, not original VexRiscv product specification.
# VPR ns units. Freeze before any Full placement/routing experiment.
create_clock -period 20.000 {clk}
'''
for direction in ('input','output'):
 ports=' '.join(patterns[direction]);sdc+=f'set_{direction}_delay -clock clk -max 2.000 [get_ports {{{ports}}}]\n';sdc+=f'set_{direction}_delay -clock clk -min 0.000 [get_ports {{{ports}}}]\n'
(D/'development.sdc').write_text(sdc);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();report=dict(bindings={str(x):sha(x) for x in (p,Path(__file__).resolve(),D/'development.sdc')},clock_ns=20,max_io_delay_ns=2,min_io_delay_ns=0,matched_ports=matched,parser_validation='NOT_YET_EXECUTED',timing_origin='Predeclared engineering development condition; not derived from native route delays or user/product deadline.',reset_model_timing='EXPERIMENTAL_PLACEHOLDER_NOT_CHARACTERIZED',unseen_family_status='UNPROVEN',scope='Static port pattern coverage and explicit development constraint freeze only; not native parser/STA/timing pass or prediction admission.')
(D/'protocol.json').write_text(json.dumps(report,indent=2)+'\n');print({k:len(v) for k,v in matched.items()},'clock20ns io2ns frozen')
