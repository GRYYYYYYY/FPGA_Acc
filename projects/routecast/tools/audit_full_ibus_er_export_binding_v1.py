"""Read-enable register binding from mapped slices to actual exported DFF."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_er_export_binding_v1_2026-10-09';D.mkdir(exist_ok=True)
N=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';P=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09';V=P/'design.v';F=P/'primitives.v';m=max(json.loads(N.read_text())['modules'].values(),key=lambda x:len(x['cells']))
assert m['netnames']['IBusCachedPlugin_cache.banks_0.s0.er']['bits']==m['netnames']['IBusCachedPlugin_cache.banks_0.s1.er']['bits']==[2693]
c=next(c for c in m['cells'].values() if c['connections'].get('Q')==[2693]);assert c['type']=='$_DFF_P_' and c['connections']['D']==[2692] and c['connections']['C']==[254]
assert '.latch b2692 b2693 re b254 0' in B.read_text();v=V.read_text();f=F.read_text()
pat=r"DFF #\(\s*\.INITIAL_VALUE\(1'b0\)\s*\) \\latch_b2693\s*\(\s*\.D\(\\latch_b2693_input_0_0 \),\s*\.Q\(\\latch_b2693_output_0_0 \),\s*\.clk\(\\latch_b2693_clock_0_0 \)\s*\);";match=re.search(pat,v);assert match
for src,dst in [('lut_b2692_output_0_0','latch_b2693_input_0_0'),('clk_output_0_0','latch_b2693_clock_0_0')]:assert re.search(r'\.datain\(\\'+src+r' \),\s*\.dataout\(\\'+dst+r' \)',v)
prim=f[f.index('module DFF #('):];prim=prim[:prim.index('endmodule')];assert 'Q <= INITIAL_VALUE;' in prim and 'always@(posedge clk)' in prim and 'Q <= D;' in prim
out={'native_register':c,'export_instance':match[0],'primitive':prim,'scope':'Both mapped bank er aliases share actual nativeQ2693. ActualexportDFF init0 samples observedready2692 on actualclock route. Thus observed preedge readyX atcycle5 predicts erX afterthatposedge; no newdirectertrace or bankpayload equality asserted.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [N,B,V,F]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(out['scope'])
