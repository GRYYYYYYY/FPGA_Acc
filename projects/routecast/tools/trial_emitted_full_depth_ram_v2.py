"""Bounded check of the exact emitted slice at actual physical width/depth."""
import hashlib
import json
import subprocess
import time
from pathlib import Path
R=Path(__file__).resolve().parents[1]; E=R/'experiments'
D=E/'emitted_full_depth_ram_v2_2026-10-09'; D.mkdir(exist_ok=False)
source=E/'full_ram_mapping_candidate_v1_2026-10-09/wrappers.v'
receipt=json.loads((source.parent/'receipt.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert receipt['exit_code']==0 and sha(source)==receipt['files'][str(source)]
y=Path(next(p for p in receipt['bindings'] if p.endswith('/bin/yosys')))
assert sha(y)==receipt['bindings'][str(y)]
text=source.read_text(); start=text.index('module rc_delayed_slice(')
slice_rtl=text[start:text.index('endmodule',start)+len('endmodule')]
(D/'slice.v').write_text(slice_rtl+'\n')
model='''module dual_port_ram #(parameter ADDR_WIDTH=10,DATA_WIDTH=20)
(input clk,we1,we2,input [ADDR_WIDTH-1:0] addr1,addr2,
input [DATA_WIDTH-1:0] data1,data2,output reg [DATA_WIDTH-1:0] out1,out2);
reg [DATA_WIDTH-1:0] mem[0:(1<<ADDR_WIDTH)-1];
always @(posedge clk) begin
out1<=mem[addr1]; out2<=mem[addr2]; if(we1) mem[addr1]<=data1;
end
endmodule
module reference(input clk,we,re,input [9:0] wa,ra,input [19:0] data,output reg [19:0] q);
reg [19:0] mem[0:1023];
always @(posedge clk) begin if(re) q<=mem[ra]; if(we) mem[wa]<=data; end
endmodule
module miter(input clk,we,re,input [9:0] wa,ra,input [19:0] data,output bad,output [19:0] golden,actual);
reference ref0(clk,we,re,wa,ra,data,golden);
rc_delayed_slice dut0(clk,we,re,wa,ra,data,actual);
assign bad=golden!=actual;
endmodule
'''
(D/'model.v').write_text(model)
script='read_verilog slice.v model.v\nhierarchy -check -top miter\nproc\nflatten\nopt\nmemory_map\nopt_clean\ncheck -assert\nsat -seq 4 -set-init-zero -prove bad 0 -show golden -show actual\n'
(D/'check.ys').write_text(script)
bindings={str(p):sha(p) for p in [Path(__file__),source,y,D/'slice.v',D/'model.v',D/'check.ys']}
command=[str(y),'-s','check.ys']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=60,
    scope='Move opt before memory expansion and only opt_clean after, avoiding measured per-bit OPT_DFF bottleneck; same exact emitted 20-bit 1024-word slice; four SAT timepoints, matched zero initial state, arbitrary binary inputs, explicit read-before-write single-write model. Not original VTR macro, arbitrary initial-state or Full sequential equivalence.'),indent=2)+'\n')
t=time.perf_counter()
with (D/'check.log').open('x') as log:
    try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
passed=code==0 and 'no model found: SUCCESS' in (D/'check.log').read_text()
out=dict(bindings=bindings,exit_code=code,seconds=time.perf_counter()-t,passed=passed,
    admitted_for_prediction=False,files={str(p):sha(p) for p in D.iterdir() if p.is_file()})
(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n')
print(code,passed,flush=True)
