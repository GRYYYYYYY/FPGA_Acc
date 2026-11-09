"""Bind observed LUT high-D to actual exported register and primitive semantics."""
import json,re,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_csr_counter_preedge_trace_v1_2026-10-09';V=D/'design.v';P=D/'primitives.v';v=V.read_text();p=P.read_text();target='$_DFF_PP0__b2016';routes={}
for port,source,suffix in [('D','lut_b2015_output_0_0','input_0_0'),('C','clk_output_0_0','clock_0_0'),('R','reset_output_0_0','input_1_0')]:
 dest=target+'_'+suffix;assert re.search(r'\.datain\(\\'+re.escape(source)+r' \),\s*\.dataout\(\\'+re.escape(dest)+r' \)',v)
 assert '.'+port+'(\\'+dest+' )' in v;routes[port]={'source':source,'register_pin':dest}
assert 'module \\$_DFF_PP0_ (input C,D,R, output reg Q);\n always @(posedge C or posedge R) if (R) Q <= 1\'b0; else Q <= D;' in p
for top in ['clk','reset']:assert re.search(r'assign \\'+top+r'_output_0_0\s*=\s*\\'+top+r'\s*;',v)
out={'routes':routes,'primitive':'positive C or positive R; R true -> Q0, otherwise Q=D','scope':'Exact exported observed D/clock/reset to real register/primitive binding. Does not establish all route delays or actual sampled trace values; those await live preedge replay.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [V,P]}}
O=R/'experiments/full_counter_high_export_register_v1_2026-10-09';O.mkdir(exist_ok=True);(O/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(routes,indent=2))
