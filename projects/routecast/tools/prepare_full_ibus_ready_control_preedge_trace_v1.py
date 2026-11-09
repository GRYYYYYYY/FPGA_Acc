"""Display-only frozen full replay IBus read control observations."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_ready_control_preedge_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(P/n,D/n)
v=(D/'design.v').read_text()
fields={'src_mmu_state':'refdut.MmuPlugin_shared_state_1','native_mmu_state':'{'+','.join('dut.\\$_DFF_PP0__b'+str(b)+'_output_0_0 ' for b in [3433,3431,3429])+'}','control_pins':'{'+','.join('dut.\\lut_new_n6085_input_0_'+str(i)+' ' for i in reversed(range(5)))+'}'}
for n in ['new_n6086','new_n6107','new_n6108','new_n6109','new_n6111']:
 fields[n]='dut.\\lut_'+n+'_output_0_0 '
for val in fields.values():
 for term in val.strip('{}').split(','):
  if term.startswith('dut.'):assert 'wire '+term[4:].strip()+' ;' in v,term
s=' $display("IBUS_CONTROL_PREEDGE cycle=%d '+' '.join(k+'=%b' for k in fields)+'",i,'+','.join(fields.values())+');\n'
tb=(P/'tb.v').read_text();a=' clk=1;#1;compare;';assert tb.count(a)==1;new=tb.replace(a,s+a);assert new.replace(s,'')==tb;(D/'tb.v').write_text(new);(D/'added_display.txt').write_text(s)
(D/'preflight.json').write_text(json.dumps({'parent':str(P.relative_to(R)),'only_display_added':True,'fields':fields,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'scope':'Observation only; original comparisons and frozen stimulus preserved. Actual exported MMU state/control6085 inputs and preceding LUT outputs observed; no initialstate or source/native state equality assumed.'},indent=2)+'\n');print(D)
