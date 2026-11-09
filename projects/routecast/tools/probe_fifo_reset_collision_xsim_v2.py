"""Reset-reachable local FIFO collision under original unmodified source RTL."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'fifo_reset_collision_xsim_v2_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';SRC=V/'vtr_flow/benchmarks/verilog/mkDelayWorker32B.v';LIB=V/'vtr_flow/primitives.v';BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);cases=[('a',32),('b',32),('c',128),('d',128),('f',60),('g',313),('x',131)];(D/'protocol.json').write_text(json.dumps({'scope':'Original generic FIFO source modules and original functional RAM library, no edits. Xvlog --relax handles unrelated full-top declaration ordering; v1 strict compile failure preserved. Synchronous active-low reset for two clock edges, then one enqueue with no dequeue from empty FIFO. Assert actual RAM writer1/read2 same address before edge; check used dout equals enqueued value. Does not prove full-top upstream reachability or arbitrary FIFO correctness.','cases':cases,'bindings':{str(p):sha(p) for p in [Path(__file__),SRC,LIB]}},indent=2)+'\n');text=[]
 for i,(suffix,w) in enumerate(cases):
  text.append(f'''`timescale 1ns/1ps
module checker{i}(output reg done=0);
reg clk=0,rst=0,clr=0,we=0,re=0;reg[{w-1}:0] din={{{w}{{1'b1}}}};wire[{w-1}:0] dout;wire full,empty;
generic_fifo_sc_{suffix} dut(.clk(clk),.rst(rst),.clr(clr),.din(din),.we(we),.re(re),.dout(dout),.full(full),.empty(empty));
initial begin
#5;clk=1;#1;#4;clk=0;#5;clk=1;#1;#4;clk=0;
if(empty !== 1'b1 || full !== 1'b0)$fatal(1,"reset flags group{i}");
rst=1;we=1;#1;
if(dut.ram1.we1 !== 1'b1 || dut.ram1.we2 !== 1'b0 || dut.ram1.addr1 !== dut.ram1.addr2 || re !== 1'b0)$fatal(1,"expected enqueue collision absent group{i}");
$display("FIFO_RESET_COLLISION group={i} writer=1 reader=2 addr=%h empty=%b full=%b re=%b",dut.ram1.addr1,empty,full,re);
#4;clk=1;#1;if(dout !== din)$fatal(1,"used own-port write-through group{i}");
$display("FIFO_USED_OWNPORT_MATCH group={i} width={w}");done=1;
end endmodule''')
 text.append('module tb;wire[6:0]done;'+''.join(f'checker{i} c{i}(done[{i}]);' for i in range(7))+'initial begin wait(&done);$display("FIFO_RESET_COLLISION_ALL7_COMPLETE");$finish;end endmodule');(D/'tb.v').write_text('\n'.join(text)+'\n');(D/'run.tcl').write_text('run all\nquit\n');rows=[]
 for cmd in [[str(BIN/'xvlog'),'--relax',str(LIB),str(SRC),str(D/'tb.v')],[str(BIN/'xelab'),'tb','-s','fifo_collision'],[str(BIN/'xsim'),'fifo_collision','-tclbatch',str(D/'run.tcl')]]:
  with (D/(Path(cmd[0]).name+'.stdout.log')).open('w') as log:code=subprocess.call(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT)
  rows.append({'command':cmd,'exit_code':code});print(Path(cmd[0]).name,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
