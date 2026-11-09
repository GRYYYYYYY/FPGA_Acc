"""Original complete MCML RTL, reset and external constant-loading stimulus only."""
import json,hashlib,subprocess,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mcml_top_collision_xsim_v2_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';SRC=V/'vtr_flow/benchmarks/verilog/mcml.v';LIB=V/'vtr_flow/primitives.v';BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);cases=['absorptionMatrix','absorptionMatrix2','absorptionMatrix3','u_cost','u_fres_down','u_fres_up','u_sint'];(D/'protocol.json').write_text(json.dumps({'scope':'Complete unmodified MCML top source/library.2active-high synchronous reset edges, external constant data1 and read_constants loading thresholds104/640/640/5120/5120 for states1..5.13000cycle bound. Observe actual RAM pins with each setup sample followed by its rising edge; v1 premature final pre-edge stop preserved; no forces/deposits/reset conversion/memory initialization. Pin collision reachability is not observable top-result mismatch or mapped equivalence. AS8GiB/core0.','cases':cases,'bindings':{str(p):sha(p) for p in [Path(__file__),SRC,LIB]}},indent=2)+'\n');checks=[]
 for i,n in enumerate(cases):
  path='dut.'+n+'.dpram1';checks.append(f'''if(!seen[{i}] && {path}.we1 === 1'b1 && {path}.we2 === 1'b0 && ^{path}.addr1 !== 1'bx && {path}.addr1 === {path}.addr2)begin
seen[{i}]=1;$display("MCML_TOP_COLLISION group={i} instance={n} cycle=%0d state=%0d addr=%h",cycle,state,{path}.addr1);end''')
 tb='''`timescale 1ns/1ps
module tb;
reg reset=1,clk=0,read_constants=0,inc_result=0;reg[31:0]constants=1;wire[3:0]state;wire[12:0]counter;reg[6:0]seen=0;integer cycle,threshold;
mcml dut(.reset(reset),.clk(clk),.constants(constants),.read_constants(read_constants),.inc_result(inc_result),.r_state(state),.r_counter(counter));
initial begin
#5;clk=1;#1;#4;clk=0;#5;clk=1;#1;#4;clk=0;reset=0;
for(cycle=0;cycle<13000;cycle=cycle+1)begin
case(state)1:threshold=104;2,3:threshold=640;4,5:threshold=5120;default:threshold=0;endcase
read_constants=threshold>0 && counter<threshold;
#1;
'''+ '\n'.join(checks)+'''
#4;clk=1;#1;
if(&seen)begin $display("MCML_TOP_ALL7_COLLISIONS_REACHED_AFTER_EDGE cycles=%0d",cycle);$finish;end
#4;clk=0;
end
$display("MCML_TOP_COLLISION_BOUND_COMPLETE seen=%b",seen);$finish;
end endmodule
''';(D/'tb.v').write_text(tb);(D/'run.tcl').write_text('run all\nquit\n');rows=[]
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 for cmd in [[str(BIN/'xvlog'),'--relax',str(LIB),str(SRC),str(D/'tb.v')],[str(BIN/'xelab'),'tb','-s','mcml_collision'],[str(BIN/'xsim'),'mcml_collision','-tclbatch',str(D/'run.tcl')]]:
  with (D/(Path(cmd[0]).name+'.stdout.log')).open('w') as log:code=subprocess.call(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  rows.append({'command':cmd,'exit_code':code});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(Path(cmd[0]).name,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
