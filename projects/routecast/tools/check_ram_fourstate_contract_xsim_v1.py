"""Original primitive HDL check of all256 A2/W1 four-state input combinations."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_fourstate_contract_xsim_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';LIB=V/'vtr_flow/primitives.v';BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);(D/'protocol.json').write_text(json.dumps({'scope':'Original functional dual_port_ram library, A2/W1 versus A11/W1 zero-extended address. Enumerate16four-state addresses*4enable*4data=256tests, each preceded by4public writes. Writer2=0, out2 unused. Inspect all4embedded stored bits and own-port outputs; check unused physical row1024 staysX. No initial memory assignments, library rewrites, source-top or delta-race equivalence claim.','bindings':{str(p):sha(p) for p in [Path(__file__),LIB]}},indent=2)+'\n');(D/'tb.v').write_text('''`timescale 1ns/1ps
module tb;
reg clk=0,we=0,data=0;reg[1:0]addr=0;wire logical_out,physical_out;reg expected[0:3];reg expected_out;integer ac,wc,dc,i,n=0;
function kind;input integer code;begin case(code)0:kind=1'b0;1:kind=1'b1;2:kind=1'bx;3:kind=1'bz;endcase end endfunction
 dual_port_ram #(.ADDR_WIDTH(2),.DATA_WIDTH(1)) logical_ram(.clk(clk),.addr1(addr),.addr2(2'b0),.data1(data),.data2(1'b0),.we1(we),.we2(1'b0),.out1(logical_out),.out2());
 dual_port_ram #(.ADDR_WIDTH(11),.DATA_WIDTH(1)) physical_ram(.clk(clk),.addr1({9'b0,addr}),.addr2(11'b0),.data1(data),.data2(1'b0),.we1(we),.we2(1'b0),.out1(physical_out),.out2());
initial begin
for(ac=0;ac<16;ac=ac+1)for(wc=0;wc<4;wc=wc+1)for(dc=0;dc<4;dc=dc+1)begin
for(i=0;i<4;i=i+1)begin addr=i;we=1;data=i%2;#5;clk=1;#1;expected[i]=data;#4;clk=0;end
addr={kind(ac/4),kind(ac%4)};we=kind(wc);data=kind(dc);
if(we===1'b1 && ^addr !== 1'bx)expected[addr]=data;
if(^addr === 1'bx)expected_out=1'bx;else expected_out=expected[addr];
#5;clk=1;#1;
if(logical_out !== expected_out || physical_out !== expected_out)$fatal(1,"own-port contract ac=%0d wc=%0d dc=%0d",ac,wc,dc);
for(i=0;i<4;i=i+1)if(logical_ram.Mem[i] !== expected[i] || physical_ram.Mem[i] !== expected[i])$fatal(1,"memory recurrence");
if(physical_ram.Mem[1024] !== 1'bx)$fatal(1,"outside row changed");
$display("FOURSTATE_CASE,%0d,%0d,%0d,%b,%b,%b",ac,wc,dc,logical_out,physical_out,expected_out);n=n+1;#4;clk=0;
end
if(n!=256)$fatal(1,"case count");$display("ORIGINAL_RAM_FOURSTATE_CONTRACT_ALL256_PASS");$finish;
end endmodule
''');(D/'run.tcl').write_text('run all\nquit\n');rows=[]
 for cmd in [[str(BIN/'xvlog'),str(LIB),str(D/'tb.v')],[str(BIN/'xelab'),'tb','-s','fourstate'],[str(BIN/'xsim'),'fourstate','-tclbatch',str(D/'run.tcl')]]:
  with (D/(Path(cmd[0]).name+'.stdout.log')).open('w') as log:code=subprocess.call(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT)
  rows.append({'command':cmd,'exit_code':code});print(Path(cmd[0]).name,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
