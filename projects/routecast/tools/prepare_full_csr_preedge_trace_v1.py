import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'full_source_export_fixed_bus_replay_v19_2026-10-09';H=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09';D=E/'full_csr_preedge_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
for n in ['reference.v','design.v','primitives.v','frozen_bus_trace.json']:shutil.copyfile(S/n,D/n)
for n in ['run.py','control.py']:shutil.copyfile(H/n,D/n)
signals={'select':'execute_CsrPlugin_csr_834','contribution':'_zz_CsrPlugin_csrMapping_readDataInit_6','cause':'CsrPlugin_mcause_exceptionCode','irq':'CsrPlugin_interrupt_code','trap':'when_CsrPlugin_l1310','trap_inner':'when_CsrPlugin_l1318','priv':'CsrPlugin_targetPrivilege','pipe_en':'when_Pipeline_l124_48','pipe_d':'decode_RS2','pipe_q':'decode_to_execute_RS2','write_en':'when_Pipeline_l124_58','write_d':'_zz_decode_RS2','execute_valid':'execute_arbitration_isValid','execute_csr':'execute_IS_CSR'}
t=(S/'tb.v').read_text();anchor=' clk=1;#1;compare;';assert t.count(anchor)==1
display=' $display("CSR_PREEDGE cycle=%d '+' '.join(k+'=%b' for k in signals)+'",i,'+','.join('refdut.'+v for v in signals.values())+');\n';(D/'tb.v').write_text(t.replace(anchor,display+anchor));(D/'added_display.txt').write_text(display)
(D/'preflight.json').write_text(json.dumps({'original_hashes':{n:hashlib.sha256((S/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json']},'phase':'Immediately before original clk=1, after original stimulus settling; read-only display.'},indent=2)+'\n');print(D)
