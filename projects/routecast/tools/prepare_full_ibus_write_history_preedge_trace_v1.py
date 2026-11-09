"""Display-only frozen full replay IBus read control observations."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_bank_history_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_write_history_preedge_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(P/n,D/n)
v=(D/'design.v').read_text()
m=max(json.loads((R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json').read_text())['modules'].values(),key=lambda x:len(x['cells']))
def probe(bit):
 for kind in ['latch','$_DFF_PP0_','lut']:
  name=kind+'_b'+str(bit)+'_output_0_0'
  if 'wire \\'+name+' ;' in v:return 'dut.\\'+name+' '
 for name,port in m['ports'].items():
  if bit in port['bits']:return 'dut.\\'+name+' ['+str(port['bits'].index(bit))+']'
 raise AssertionError(bit)
def vec(bits):return '{'+','.join(probe(b) for b in reversed(bits))+'}'
pa=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pa']['bits']
pd=m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pd']['bits']+m['netnames']['IBusCachedPlugin_cache.banks_0.s1.pd']['bits'][:12]
fields={'native_wa':vec(m['netnames']['IBusCachedPlugin_cache.banks_0.WA']['bits']),'native_pa':vec(pa),'native_pd':vec(pd)}
s=' $display("IBUS_WRITE_PREEDGE cycle=%d '+' '.join(k+'=%b' for k in fields)+'",i,'+','.join(fields.values())+');\n'
tb=(P/'tb.v').read_text();a=' clk=1;#1;compare;';assert tb.count(a)==1;new=tb.replace(a,s+a);assert new.replace(s,'')==tb;(D/'tb.v').write_text(new);(D/'added_display.txt').write_text(s)
(D/'preflight.json').write_text(json.dumps({'parent':str(P.relative_to(R)),'only_display_added':True,'fields':fields,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'scope':'Observation only; original comparisons and frozen stimulus preserved. Actual source bank Q/write enable/address/data/read address and native visible32bits/held32bits/er/pw/hit observed. No initial bank contents or source/native payload equality assumed.'},indent=2)+'\n');print(D)
