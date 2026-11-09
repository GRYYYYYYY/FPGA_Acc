"""Add only preedge capture-operand displays to validated complete replay."""
import shutil,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/full_csr_selector_native_trace_v1_2026-10-09';D=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
assert json.loads((P/'trace_audit.json').read_text())['replay_fidelity']
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(P/n,D/n)
v=(D/'design.v').read_text();fields={}
for node in ['new_n5324','new_n5374','new_n5367','new_n5366','new_n5375','new_n5938','new_n5940','new_n5937']:
 wire='lut_'+node+'_output_0_0';assert 'wire \\'+wire+' ;' in v;fields[node]='dut.\\'+wire+' '
display=' $display("CSR_CAPTURE_OPERANDS cycle=%d '+' '.join(k+'=%b' for k in fields)+'",i,'+','.join(fields.values())+');\n'
tb=(P/'tb.v').read_text();anchor=' clk=1;#1;compare;';assert tb.count(anchor)==1;new=tb.replace(anchor,display+anchor);assert new.replace(display,'')==tb;(D/'tb.v').write_text(new);(D/'added_display.txt').write_text(display)
(D/'preflight.json').write_text(json.dumps({'parent':str(P.relative_to(R)),'fields':fields,'only_display_added':True,'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','tb.v']},'scope':'Full frozen original comparison retained; no initialized unknown values or functional admission.'},indent=2)+'\n');print(str(D))
