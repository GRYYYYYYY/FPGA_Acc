"""Display-only original/export selector and decode capture observations."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_native_tag_access_path_trace_v1_2026-10-09';D=R/'experiments/full_csr_selector_native_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(P/n,D/n)
m=max(json.loads((R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json').read_text())['modules'].values(),key=lambda m:len(m['cells']))
v=(D/'design.v').read_text()
def probe(b,kind):
 name=kind+'_b'+str(b)+'_output_0_0';assert 'wire \\'+name+' ;' in v,name;return 'dut.\\'+name+' '
names=['execute_CsrPlugin_csr_'+str(i) for i in [768,256,384,836,772,833,834,835]]
assert 'wire \\lut_new_n5937_output_0_0 ;' in v
fields={'src_en':'refdut.when_CsrPlugin_l1589','src_instruction':'refdut.decode_INSTRUCTION[31:20]','src_select':'{'+','.join('refdut.'+n for n in reversed(names))+'}','native_capture_node':'dut.\\lut_new_n5937_output_0_0 ','native_instruction':'{'+','.join(probe(b,'latch') for b in reversed(m['netnames']['decode_INSTRUCTION']['bits'][20:32]))+'}','native_select':'{'+','.join(probe(m['netnames'][n]['bits'][0],'latch') for n in reversed(names))+'}'}
display=' $display("CSR_SELECTOR_PREEDGE cycle=%d '+' '.join(k+'=%b' for k in fields)+'",i,'+','.join(fields.values())+');\n'
tb=(P/'tb.v').read_text();anchor=' clk=1;#1;compare;';assert tb.count(anchor)==1;new=tb.replace(anchor,display+anchor);assert new.replace(display,'')==tb;(D/'tb.v').write_text(new);(D/'added_display.txt').write_text(display)
out={'parent':str(P.relative_to(R)),'fields':fields,'only_display_added':True,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'scope':'Observation only; full original comparisons/stimulus preserved. No functional admission.'};(D/'preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'directory':str(D),'fields':list(fields)}))
