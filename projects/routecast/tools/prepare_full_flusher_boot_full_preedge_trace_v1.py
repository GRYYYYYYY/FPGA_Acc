"""Display-only frozen full replay IBus read control observations."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_ibus_fill_capture_preedge_trace_v1_2026-10-09';D=R/'experiments/full_flusher_boot_full_preedge_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(P/n,D/n)
v=(D/'design.v').read_text()
m=max(json.loads((R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json').read_text())['modules'].values(),key=lambda x:len(x['cells']))
def probe(bit):
 for kind in ['latch','$_DFF_PP0_','$_DFF_PP1_','lut']:
  name=kind+'_b'+str(bit)+'_output_0_0'
  if 'wire \\'+name+' ;' in v:return 'dut.\\'+name+' '
 for name,port in m['ports'].items():
  if bit in port['bits']:return 'dut.\\'+name+' ['+str(port['bits'].index(bit))+']'
 raise AssertionError(bit)
def vec(bits):return '{'+','.join(probe(b) for b in reversed(bits))+'}'
qs=m['netnames']['dataCache_1.stageB_flusher_counter']['bits']
def dprobe(q):
 c=next(c for c in m['cells'].values() if c['connections'].get('Q')==[q]);name='lut_b'+str(c['connections']['D'][0])+'_output_0_0';assert 'wire \\'+name+' ;' in v;return 'dut.\\'+name+' '
fields={'reset':'reset','src_counter':'refdut.dataCache_1.stageB_flusher_counter','src_start':'refdut.dataCache_1.stageB_flusher_start','src_singleLine':'refdut.dataCache_1.io_cpu_flush_payload_singleLine','src_lineId':'refdut.dataCache_1.io_cpu_flush_payload_lineId','src_increment':'refdut.dataCache_1.when_DataCache_l850 && refdut.dataCache_1.when_DataCache_l856','native_Q':vec(qs),'native_D':'{'+','.join(dprobe(q) for q in reversed(qs))+'}','native_start':probe(3121),'native_zero_instruction':'dut.\\lut_new_n6607_output_0_0 ','native_lineId':vec(m['netnames']['dataCache_1.io_cpu_flush_payload_lineId']['bits']),'native_instruction':vec(m['netnames']['execute_INSTRUCTION']['bits'][15:20])}
s=' $display("FLUSH_BOOT_PREEDGE cycle=%d '+' '.join(k+'=%b' for k in fields)+'",i,'+','.join(fields.values())+');\n'
tb=(P/'tb.v').read_text();a=' clk=1;#1;compare;';assert tb.count(a)==1;new=tb.replace(a,s+a);assert new.replace(s,'')==tb;(D/'tb.v').write_text(new);(D/'added_display.txt').write_text(s)
(D/'preflight.json').write_text(json.dumps({'parent':str(P.relative_to(R)),'only_display_added':True,'fields':fields,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'scope':'Observation only; original comparisons and frozen stimulus preserved. Actual full counter8Q/D, reset/start, lineId7, singleLine detector and instruction5 observed; original source/comparison/stimulus preserved. No invented initial state.'},indent=2)+'\n');print(D)
