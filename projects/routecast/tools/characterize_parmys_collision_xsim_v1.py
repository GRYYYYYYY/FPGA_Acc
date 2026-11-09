"""Collision diagnostic; swapped process order is never an admitted source change."""
import json,hashlib,subprocess,re,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/parmys_collision_xsim_v1_2026-10-21';P=R/'experiments/parmys_registered_bank_xsim_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';B=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);lib=V/'vtr_flow/primitives.v';text=lib.read_text();mod=text[text.index('module dual_port_ram'):];mod=mod[:mod.index('endmodule')+len('endmodule')];start=mod.index('    always@(posedge clk)');second=mod.index('    always@(posedge clk)',start+1);end=mod.rindex('endmodule');swapped=mod[:start]+mod[second:end]+mod[start:second]+'endmodule\n';swapped=swapped.replace('module dual_port_ram','module diagnostic_swapped_ram',1);diag=D/'diagnostic_swapped.v';diag.write_text(swapped);protocol={'scope':'256 same-address writes/reads per actual repaired mapped shape, full public-write initialization of two rows per bank. Original library reference and mapped modules unchanged. Additional source-process-order-swapped reference is a diagnostic ONLY, not a proposed fix or canonical model. No new native labels or reset/clock/source admission.','bindings':{str(p):sha(p) for p in [Path(__file__),lib,diag,P/'dp13x32/mapped.v',P/'dp16x36/mapped.v']}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for name,a,w in [('dp13x32',13,32),('dp16x36',16,36)]:
  f=D/name;f.mkdir();size=1<<(a-10)
  tb=f'''`timescale 1ns/1ps
module tb;
reg clk=0;reg [{a-1}:0] addr1=0,addr2=17;reg [{w-1}:0] data1=0;reg we1=0;
wire [{w-1}:0] r1,r2,m1,m2,s1,s2;reg [{w-1}:0] score[0:{size-1}];reg [{w-1}:0] old;integer j,i;
dual_port_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) reference(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.data2({w}'b0),.we1(we1),.we2(1'b0),.out1(r1),.out2(r2));
diagnostic_swapped_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) diagnostic(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.data2({w}'b0),.we1(we1),.we2(1'b0),.out1(s1),.out2(s2));
mapped_probe mapped(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.we1(we1),.out1(m1),.out2(m2));
initial begin
for(i=0;i<{size};i=i+1) begin
addr1=i;addr2=17;data1=i*37+5;we1=1;#5;clk=1;#1;
if(r1 !== data1 || m1 !== data1 || s1 !== data1)$fatal(1,"init own-port mismatch");score[i]=data1;#4;clk=0;
end
for(j=0;j<256;j=j+1)begin
addr1=j%{size};addr2=addr1;old=score[addr1];data1=~old;we1=1;
#5;clk=1;#1;
if(r1 !== data1 || m1 !== data1 || s1 !== data1)$fatal(1,"collision own-port mismatch");
$display("COLLISION,%0d,%0d,%h,%h,%h,%h,%h",j,addr1,old,data1,r2,m2,s2);
score[addr1]=data1;#4;clk=0;
end
$display("COLLISION_DIAGNOSTIC_COMPLETE cycles=256");$finish;
end
endmodule
''';(f/'tb.v').write_text(tb);(f/'run.tcl').write_text('run all\nquit\n');stages=[]
  for cmd in [[str(B/'xvlog'),str(lib),str(diag),str(P/name/'mapped.v'),str(f/'tb.v')],[str(B/'xelab'),'tb','-s','collision'],[str(B/'xsim'),'collision','-tclbatch',str(f/'run.tcl')]]:
   tick=time.monotonic()
   with (f/(Path(cmd[0]).name+'.stdout.log')).open('w') as out:code=subprocess.call(cmd,cwd=f,stdout=out,stderr=subprocess.STDOUT)
   stages.append({'command':cmd,'exit_code':code,'seconds':time.monotonic()-tick});print(name,Path(cmd[0]).name,code,flush=True)
   if code:break
  rows.append({'case':name,'stages':stages});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
