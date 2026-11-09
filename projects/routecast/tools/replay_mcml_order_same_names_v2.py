"""Matched separate HDL runs, identical source/TB/names/externally frozen input schedule."""
import json,hashlib,subprocess,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mcml_collision_order_same_names_v2_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';SRC=V/'vtr_flow/benchmarks/verilog/mcml.v';LIB=V/'vtr_flow/primitives.v';BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);text=LIB.read_text();start=text.index('module dual_port_ram');a=text.index('    always@(posedge clk)',start);b=text.index('    always@(posedge clk)',a+1);end=text.index('endmodule',b);swapped=text[:a]+text[b:end]+text[a:b]+text[end:];diag=D/'swapped_primitives.v';diag.write_text(swapped);obj=json.loads((E/'preserved_source_ram_mapping_v1_2026-10-21/mcml/preserved_boundary.json').read_text())['modules']['mcml'];outputs={n:len(p['bits']) for n,p in obj['ports'].items() if p['direction']=='output'};cases=['absorptionMatrix','absorptionMatrix2','absorptionMatrix3','u_cost','u_fres_down','u_fres_up','u_sint'];intervals=[];begin=0
 for length in [104,640,640,5120,5120]:intervals.append([begin,begin+length]);begin+=length+1
 decl=[];ports=[];expressions=[];fields=[]
 for i,(n,w) in enumerate(outputs.items()):decl.append(f'wire[{w-1}:0]o{i};');ports.append(f'.{n}(o{i})');expressions.append(f'o{i}');fields.append('top:'+n)
 for n in cases:expressions.append(f'dut.{n}.dpram1.out2');fields.append('ram:'+n)
 stim=' || '.join(f'(cycle>={a} && cycle<{b})' for a,b in intervals);format_string='FRAME,%0d,%b'+',%h'*len(expressions)
 tb='''`timescale 1ns/1ps
module tb;
reg reset=1,clk=0,read_constants=0,inc_result=0;reg[31:0]constants=1;integer cycle;
'''+ '\n'.join(decl)+'\nmcml dut(.reset(reset),.clk(clk),.constants(constants),.read_constants(read_constants),.inc_result(inc_result),'+','.join(ports)+');\n'+'''initial begin
#5;clk=1;#1;#4;clk=0;#5;clk=1;#1;#4;clk=0;reset=0;
for(cycle=0;cycle<90000;cycle=cycle+1)begin
read_constants='''+stim+''';#5;clk=1;#1;
$display("'''+format_string+'",cycle,read_constants,'+','.join(expressions)+''');
#4;clk=0;
end
$display("MATCHED_ORDER_REPLAY_COMPLETE cycles=90000");$finish;
end endmodule
''';(D/'tb.v').write_text(tb);(D/'protocol.json').write_text(json.dumps({'scope':'Separate runs with same original complete MCML source, same TB, same module/instance names, fixed external input schedule and flags. Only library dual_port_ram always-block textual order changes. Capture every declared top output and7RAM out2 values after each edge for90000cycles. Diagnostic only, not mapped equivalence or canonical RAM source change.','fields':fields,'read_constants_intervals_half_open':intervals,'bindings':{str(p):sha(p) for p in [Path(__file__),SRC,LIB,diag,D/'tb.v']}},indent=2)+'\n');rows=[]
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 for arm,library in [('original',LIB),('swapped',diag)]:
  f=D/arm;f.mkdir();(f/'run.tcl').write_text('run all\nquit\n')
  for cmd in [[str(BIN/'xvlog'),'--relax',str(library),str(SRC),str(D/'tb.v')],[str(BIN/'xelab'),'tb','-s','matched_order'],[str(BIN/'xsim'),'matched_order','-tclbatch',str(f/'run.tcl')]]:
   with (f/(Path(cmd[0]).name+'.stdout.log')).open('w') as log:code=subprocess.call(cmd,cwd=f,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
   rows.append({'arm':arm,'command':cmd,'exit_code':code});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(arm,Path(cmd[0]).name,code,flush=True)
   if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
