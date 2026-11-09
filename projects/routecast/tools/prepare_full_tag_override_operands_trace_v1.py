import hashlib,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'full_tag_write_override_preedge_trace_v1_2026-10-09';D=E/'full_tag_override_operands_trace_v1_2026-10-09';D.mkdir(exist_ok=True)
a=json.loads((S/'trace_audit.json').read_text());assert a['replay_fidelity'] and all(r['exit_code']==0 for r in a['stages'])
for name in ['reference.v','design.v','primitives.v','frozen_bus_trace.json','run.py','control.py']:shutil.copyfile(S/name,D/name)
source=['stageB_consistancyHazard','stageB_mmuRsp_refilling','io_cpu_writeBack_accessError','io_cpu_writeBack_mmuException','io_cpu_writeBack_unalignedAccess','when_DataCache_l824','stageB_mmuRspFreeze','io_cpu_writeBack_isStuck','io_cpu_memory_mmuRsp_refilling']
signals={name:'refdut.dataCache_1.'+name for name in source}
signals['native_refilling']='dut.\\latch_b1928_output_0_0 '
for lane in [0,2,3,4]:signals['allow_input'+str(lane)]='dut.\\lut_new_n5367_input_0_'+str(lane)+' '
t=(S/'tb.v').read_text();anchor=' clk=1;#1;compare;';assert t.count(anchor)==1
display=' $display("TAG_OVERRIDE_OPERANDS cycle=%d '+' '.join(k+'=%b' for k in signals)+'",i,'+','.join(signals.values())+');\n';(D/'tb.v').write_text(t.replace(anchor,display+anchor));(D/'added_display.txt').write_text(display)
(D/'preflight.json').write_text(json.dumps({'parent':str(S),'signals':signals,'original_hashes':{name:hashlib.sha256((S/name).read_bytes()).hexdigest() for name in ['reference.v','design.v','primitives.v','tb.v','frozen_bus_trace.json','run.py','control.py']},'scope':'Only read-only pre-edge display added; no design/stimulus change.'},indent=2)+'\n');print(D)
