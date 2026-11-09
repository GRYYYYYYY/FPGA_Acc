"""Read-enable register binding from mapped slices to actual exported DFF."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_pw_export_binding_v1_2026-10-09';D.mkdir(exist_ok=True)
N=R/'experiments/full_native_ram_gates_v3_2026-10-09/gates.json';B=R/'experiments/full_ram_init_export_runtime_v8_2026-10-09/design.blif';P=R/'experiments/full_ibus_ready_preedge_trace_v1_2026-10-09';V=P/'design.v';F=P/'primitives.v';m=max(json.loads(N.read_text())['modules'].values(),key=lambda x:len(x['cells']))
assert m['netnames']['IBusCachedPlugin_cache.banks_0.s0.pw']['bits']==m['netnames']['IBusCachedPlugin_cache.banks_0.s1.pw']['bits']==[2691]
c=next(c for c in m['cells'].values() if c['connections'].get('Q')==[2691]);assert c['type']=='$_DFF_P_' and c['connections']['D']==[220] and c['connections']['C']==[254]
assert '.latch b220 b2691 re b254 0' in B.read_text();v=V.read_text();f=F.read_text()
pat=r"DFF #\(\s*\.INITIAL_VALUE\(1'b0\)\s*\) \\latch_b2691\s*\(\s*\.D\(\\latch_b2691_input_0_0 \),\s*\.Q\(\\latch_b2691_output_0_0 \),\s*\.clk\(\\latch_b2691_clock_0_0 \)\s*\);";match=re.search(pat,v);assert match
for src,dst in [('iBus_rsp_valid_output_0_0','latch_b2691_input_0_0'),('clk_output_0_0','latch_b2691_clock_0_0')]:assert re.search(r'\.datain\(\\'+src+r' \),\s*\.dataout\(\\'+dst+r' \)',v)
assert 'assign \\iBus_rsp_valid_output_0_0  = \\iBus_rsp_valid ;' in v
assert m['ports']['iBus_rsp_valid']['bits']==[220]
prim=f[f.index('module DFF #('):];prim=prim[:prim.index('endmodule')];assert 'Q <= INITIAL_VALUE;' in prim and 'always@(posedge clk)' in prim and 'Q <= D;' in prim
out={'native_register':c,'export_instance':match[0],'primitive':prim,'scope':'Both mapped bank pending-write aliases share actual nativeQ2691. ActualexportDFF init0 samples common top iBus_rsp_valid through actual top-input buffer and clock route. Input history known in frozen replay; delayed write address/payload and raw-array correspondence remain separate.','hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [N,B,V,F]}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(out['scope'])
