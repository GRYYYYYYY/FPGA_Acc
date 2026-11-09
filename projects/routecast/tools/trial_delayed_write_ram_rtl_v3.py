"""Bounded actual RTL check using original VTR dual_port_ram behavior."""
import json,hashlib,subprocess,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'delayed_write_ram_rtl_v3_2026-10-09';D.mkdir(exist_ok=False);root=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';source=root/'vtr_flow/primitives.v';plan=json.loads((E/'vexriscv_family_flattened_inventory_v1_2026-10-09/protocol.json').read_text());y=Path(next(p for p in plan['bindings'] if p.endswith('/bin/yosys')));shutil.copyfile(source,D/'primitives.v')
rtl='''module old_reference(input clk, we, re, input [1:0] wa,ra,data, output reg [1:0] q);
reg [1:0] mem[0:3]; always @(posedge clk) begin if(re) q<=mem[ra]; if(we) mem[wa]<=data; end
endmodule
module delayed_wrapper(input clk,we,re,input [1:0] wa,ra,data,output [1:0] q);
reg pw=0, er=0,hit; reg [1:0] pa,pd,fwd,held; wire [1:0] raw,unused;
canonical_one_write_dp #(.ADDR_WIDTH(2),.DATA_WIDTH(2)) ram(.clk(clk),.we1(pw),.addr1(pa),.data1(pd),.out1(unused),.we2(1'b0),.addr2(ra),.data2(2'b00),.out2(raw));
assign q=er ? (hit ? fwd : raw) : held;
always @(posedge clk) begin held<=q;er<=re;hit<=pw && pa==ra;fwd<=pd;pw<=we;pa<=wa;pd<=data;end
endmodule
module miter(input clk,we,re,input [1:0] wa,ra,data,output bad,output [1:0] golden,actual);
old_reference ref0(clk,we,re,wa,ra,data,golden); delayed_wrapper dut0(clk,we,re,wa,ra,data,actual); assign bad=golden!=actual;
endmodule
''';rtl+='''
module canonical_one_write_dp #(parameter ADDR_WIDTH=2,DATA_WIDTH=2)(input clk,we1,we2,input [ADDR_WIDTH-1:0] addr1,addr2,input [DATA_WIDTH-1:0] data1,data2,output reg [DATA_WIDTH-1:0] out1,out2);
reg [DATA_WIDTH-1:0] mem[0:(1<<ADDR_WIDTH)-1];
always @(posedge clk) begin if(we1) mem[addr1]=data1;out1=mem[addr1];out2=mem[addr2];end
endmodule
''';(D/'wrapper.v').write_text(rtl);script='read_verilog primitives.v wrapper.v\nhierarchy -check -top miter\nproc\nsetattr -mod -unset keep_hierarchy\nsetattr -unset keep_hierarchy\nflatten\nmemory_map\nopt\ncheck -assert\nsat -seq 6 -set-init-zero -prove bad 0 -show golden -show actual\n';(D/'check.ys').write_text(script);sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();bindings={str(p):sha(p) for p in (Path(__file__).resolve(),source,y,D/'wrapper.v',D/'check.ys')};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,timeout_s=60,scope='Bounded six timepoints, two-bit four-word explicit canonical single-write dual-read model and actual wrapper RTL, common zero initial memory/output, arbitrary binary control inputs; not original VTR macro behavior proof. Not arbitrary-depth induction, four-state simulation or Full mapping.'),indent=2)+'\n')
with (D/'check.log').open('x') as log:
 try:code=subprocess.run([str(y),'-s','check.ys'],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
 except subprocess.TimeoutExpired:code='TIMEOUT'
passed=code==0 and 'no model found: SUCCESS' in (D/'check.log').read_text();(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,exit_code=code,passed=passed,files={str(p):sha(p) for p in D.iterdir() if p.is_file()}),indent=2)+'\n');print(code,passed)
