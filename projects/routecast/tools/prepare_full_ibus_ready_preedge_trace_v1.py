"""Display-only frozen full replay IBus read control observations."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09';D=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(P/n,D/n)
v=(D/'design.v').read_text()
fields={'src_busy':'refdut.IBusCachedPlugin_mmuBus_busy','src_stuck':'refdut.decode_arbitration_isStuck','src_issue':'refdut.IBusCachedPlugin_rsp_issueDetected_4','src_ready':'refdut.IBusCachedPlugin_iBusRsp_stages_1_input_ready','src_bank_re':'!refdut.IBusCachedPlugin_cache.io_cpu_fetch_isStuck','native_ready':'dut.\\lut_b2692_output_0_0 ','native_ready_pins':'{'+','.join('dut.\\lut_b2692_input_0_'+str(i)+' ' for i in reversed(range(5)))+'}'}
for n in ['lut_b2692_output_0_0']+['lut_b2692_input_0_'+str(i) for i in range(5)]:assert 'wire \\'+n+' ;' in v
src=(D/'reference.v').read_text();assert 'io_cpu_fetch_isStuck' in src
s=' $display("IBUS_READY_PREEDGE cycle=%d '+' '.join(k+'=%b' for k in fields)+'",i,'+','.join(fields.values())+');\n'
tb=(P/'tb.v').read_text();a=' clk=1;#1;compare;';assert tb.count(a)==1;new=tb.replace(a,s+a);assert new.replace(s,'')==tb;(D/'tb.v').write_text(new);(D/'added_display.txt').write_text(s)
(D/'preflight.json').write_text(json.dumps({'parent':str(P.relative_to(R)),'only_display_added':True,'fields':fields,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'scope':'Observation only; original comparisons and frozen stimulus preserved. Native LUT ready/pins are actual export probes; source issue/stuck not assumed equal to native internal controls.'},indent=2)+'\n');print(D)
