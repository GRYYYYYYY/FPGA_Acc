import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09';H=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09';D=E/'full_flush_capture_preedge_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:shutil.copyfile(S/n,D/n)
for n in ['run.py','control.py']:shutil.copyfile(H/n,D/n)
s={'src_q':'refdut.dataCache_1.stageB_flusher_counter','src_start':'refdut.dataCache_1.stageB_flusher_start','src_single':'refdut.dataCache_1.io_cpu_flush_payload_singleLine','src_line':'refdut.dataCache_1.io_cpu_flush_payload_lineId','src_increment':'refdut.dataCache_1.when_DataCache_l856','native_q6':'dut.\\$_DFF_PP0__b2014 .Q','native_d6':'dut.\\$_DFF_PP0__b2014 .D','native_q7':'dut.\\$_DFF_PP0__b2016 .Q','native_d7':'dut.\\$_DFF_PP0__b2016 .D','native_start':'dut.\\$_DFF_PP1__b3121 .Q','native_gate':'dut.\\lut_new_n6607_output_0_0 ','native_carry':'dut.\\lut_new_n6618_output_0_0 ','native_d6_inputs':'{dut.\\lut_b2013_input_0_5 ,dut.\\lut_b2013_input_0_4 ,dut.\\lut_b2013_input_0_3 ,dut.\\lut_b2013_input_0_2 ,dut.\\lut_b2013_input_0_1 ,dut.\\lut_b2013_input_0_0 }'}
t=(S/'tb.v').read_text();additions=[]
for phase,anchor in [('PRE',' clk=1;#1;compare;'),('POST',' #4;clk=0;if(i==2)')]:
 assert t.count(anchor)==1
 display=' if(i<8) $display("FLUSH_CAPTURE_'+phase+' cycle=%d reset=%b '+' '.join(k+'=%b' for k in s)+'",i,reset,'+','.join(s.values())+');\n';additions.append(display);t=t.replace(anchor,display+anchor)
(D/'tb.v').write_text(t);(D/'added_displays.json').write_text(json.dumps(additions,indent=2)+'\n');(D/'preflight.json').write_text(json.dumps({'original_hashes':{n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'scope':'Eight pre/post-edge read-only observations; complete512-cycle stimulus and comparison unchanged.'},indent=2)+'\n');print(D)
