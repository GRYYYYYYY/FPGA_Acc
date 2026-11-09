"""Reachable binary reset-release counterexample; no forced/internal state."""
import json,subprocess
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_reset_counterexample_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);usr=E/'prospective_external_family_sim_runtime_v1_2026-10-18/root/usr';iv=usr/'bin/iverilog';vvp=usr/'bin/vvp';lib=usr/'lib/x86_64-linux-gnu/ivl';sim=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/share/yosys/simcells.v';tb=D/'counterexample_tb.v';tb.write_text(r'''`timescale 1ns/1ps
module counterexample_tb;
reg C=0;reg R=1;
wire RI=~R;wire g0,n0,g1,n1;
\$_DFF_PN0_ G0(.C(C),.R(R),.D(1'b1),.Q(g0));
\$_DFF_PP0_ N0(.C(C),.R(RI),.D(1'b1),.Q(n0));
\$_DFF_PN1_ G1(.C(C),.R(R),.D(1'b0),.Q(g1));
\$_DFF_PP1_ N1(.C(C),.R(RI),.D(1'b0),.Q(n1));
initial begin
#2;R=0;#2;
if(g0!==0 || n0!==0 || g1!==1 || n1!==1) $fatal(1,"reset establishment failed");
$display("ESTABLISHED_RESET C=%b R=%b gold0=%b normalized0=%b gold1=%b normalized1=%b",C,R,g0,n0,g1,n1);
#2;C<=1;R<=1;#1;
$display("COUNTEREXAMPLE C=%b R=%b gold0=%b normalized0=%b gold1=%b normalized1=%b",C,R,g0,n0,g1,n1);
if(g0!==1 || n0!==0 || g1!==0 || n1!==1) $fatal(1,"expected pinned scheduling counterexample missing");
$display("REACHABLE_BINARY_COUNTEREXAMPLE_CONFIRMED_NO_FORCE");$finish;
end
endmodule
''');image=D/'counterexample.vvp';cc=[str(iv),'-B',str(lib),'-g2012','-s','counterexample_tb','-o',str(image),str(sim),str(tb)];sc=[str(vvp),'-M',str(lib),str(image)];bindings={str(p):sha(p) for p in [Path(__file__),tb,iv,vvp,sim,E/'prince_reset_event_sim_v1_2026-10-20/receipt.json']};(D/'protocol.json').write_text(json.dumps({'compile_command':cc,'simulation_command':sc,'bindings':bindings,'scope':'Pinned-simulator reachable binary primitive counterexample, explicit reset assertion then simultaneous nonblocking clock-rise/reset-release. No force/release or state injection. Does not claim every scheduler, full circuit failure or physical hardware behavior.'},indent=2)+'\n')
 for name,command in [('compile',cc),('simulation',sc)]:
  with (D/(name+'.log')).open('x') as log:code=subprocess.call(command,stdout=log,stderr=subprocess.STDOUT)
  assert code==0
 assert 'REACHABLE_BINARY_COUNTEREXAMPLE_CONFIRMED_NO_FORCE' in (D/'simulation.log').read_text();(D/'verification.json').write_text(json.dumps({'status':'REACHABLE_BINARY_COUNTEREXAMPLE_REPRODUCED_WITHOUT_FORCE','reset_zero_pair':{'original_Q':1,'normalized_Q':0},'reset_one_pair':{'original_Q':0,'normalized_Q':1},'unconditional_polarity_normalization_admitted':False,'native_labels_generated':False,'bindings':{str(p):sha(p) for p in [D/'protocol.json',D/'compile.log',D/'simulation.log',image]},'scope':'Refutes unconditional simulation equivalence in this pinned event scheduling. No timing assumption added to bypass result.'},indent=2)+'\n');print('REACHABLE_BINARY_RESET_COUNTEREXAMPLE_CONFIRMED')
if __name__=='__main__':main()
