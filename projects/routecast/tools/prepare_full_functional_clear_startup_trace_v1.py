import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';src=E/'full_source_export_fixed_bus_replay_v19_2026-10-09';helper=E/'full_source_export_startup_tag_write_trace_v21_2026-10-09';out=E/'full_functional_clear_startup_trace_v1_2026-10-09';out.mkdir(exist_ok=True)
for n in ['primitives.v','reference.v','design.v','frozen_bus_trace.json']:shutil.copyfile(src/n,out/n)
for n in ['run.py','control.py']:shutil.copyfile(helper/n,out/n)
t= (src/'tb.v').read_text()
(out/'tb_original.v').write_text(t)
(out/'preflight.json').write_text(json.dumps({'original_hashes':{n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in ['reference.v','design.v','tb.v','frozen_bus_trace.json']},'scope':'Read-only source-state displays; original frozen stimulus and external comparison retained.'},indent=2)+'\n')

signals={'dc_en':'dataCache_1.when_DataCache_l824','io':'dataCache_1.stageB_mmuRsp_isIoAccess','refill':'dataCache_1.stageB_mmuRsp_refilling','exception':'dataCache_1.stageB_mmuRsp_exception','aw':'dataCache_1.stageB_mmuRsp_allowWrite','ar':'dataCache_1.stageB_mmuRsp_allowRead','pipe_en':'when_Pipeline_l124_19','pipe_q':'decode_to_execute_REGFILE_WRITE_VALID','irq_en':'when_CsrPlugin_l1216','irq_q':'CsrPlugin_interrupt_code','trap_en':'when_CsrPlugin_l1310','trap_inner':'when_CsrPlugin_l1318','priv':'CsrPlugin_targetPrivilege','cause':'CsrPlugin_mcause_exceptionCode','wb':'writeBack_arbitration_isValid','debug_en':'when_DebugPlugin_l308','debug_q':'DebugPlugin_busReadDataReg'}
anchor=' #4;clk=0;if(i==2)';assert t.count(anchor)==1
display=' $display("FUNCTIONAL_CLEAR cycle=%d '+' '.join(k+'=%b' for k in signals)+'",i,'+','.join('refdut.'+v for v in signals.values())+');\n'
(out/'tb.v').write_text(t.replace(anchor,display+anchor));(out/'added_display.txt').write_text(display)
