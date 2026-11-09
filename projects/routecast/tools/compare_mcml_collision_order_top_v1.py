"""Complete-top sensitivity diagnostic, never a proposed RTL/reference replacement."""
import json,re,hashlib,subprocess,resource
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'mcml_collision_order_top_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';SRC=V/'vtr_flow/benchmarks/verilog/mcml.v';LIB=V/'vtr_flow/primitives.v';BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);source=SRC.read_text();modules=re.findall(r'^\s*module\s+(\w+)',source,re.M);assert modules and len(modules)==len(set(modules));rename={n:n+'_rc_orderdiag' for n in modules};rename['dual_port_ram']='diagnostic_swapped_ram';tokens=re.compile(r'\b(?:'+'|'.join(map(re.escape,sorted(rename,key=len,reverse=True)))+r')\b');diag=tokens.sub(lambda m:rename[m[0]],source);(D/'diagnostic_mcml.v').write_text(diag);lib=LIB.read_text();ram=lib[lib.index('module dual_port_ram'):];ram=ram[:ram.index('endmodule')+len('endmodule')];start=ram.index('    always@(posedge clk)');second=ram.index('    always@(posedge clk)',start+1);end=ram.rindex('endmodule');swapped=ram[:start]+ram[second:end]+ram[start:second]+'endmodule\n';swapped=swapped.replace('module dual_port_ram','module diagnostic_swapped_ram',1);(D/'diagnostic_ram.v').write_text(swapped);m=json.loads((E/'preserved_source_ram_mapping_v1_2026-10-21/mcml/preserved_boundary.json').read_text())['modules']['mcml'];outputs={k:len(v['bits']) for k,v in m['ports'].items() if v['direction']=='output'};(D/'protocol.json').write_text(json.dumps({'scope':'Original full MCML source versus alpha-renamed diagnostic copy with RAM always-block order swapped ONLY. Same external reset/loading stimulus,90000post-reset cycles to include load/clear/calc. Compare all declared top output bits four-state, and RAM out2 differences separately. Not canonical read-mode selection, mapped equivalence, valid application coefficient claim or proposed source change. Source/library originals unchanged. AS8GiB/core0.','renamed_modules':rename,'outputs':outputs,'bindings':{str(p):sha(p) for p in [Path(__file__),SRC,LIB,D/'diagnostic_mcml.v',D/'diagnostic_ram.v']}},indent=2)+'\n');decl=[];portsA=[];portsB=[];comparisons=[];summary=[]
 for i,(n,w) in enumerate(outputs.items()):
  decl.append(f'wire[{w-1}:0]a{i},b{i};integer diff{i}=0;');portsA.append(f'.{n}(a{i})');portsB.append(f'.{n}(b{i})');comparisons.append(f'if(a{i} !== b{i})begin if(diff{i}==0)$display("TOP_FIRST_DIFFERENCE port={n} cycle=%0d original=%h diagnostic=%h",cycle,a{i},b{i});diff{i}=diff{i}+1;end');summary.append(f'$display("TOP_OUTPUT_SUMMARY port={n} differing_cycles=%0d",diff{i});')
 cases=['absorptionMatrix','absorptionMatrix2','absorptionMatrix3','u_cost','u_fres_down','u_fres_up','u_sint'];monitors=[];ram_summary=[]
 for i,n in enumerate(cases):
  decl.append(f'integer ramdiff{i}=0;');monitors.append(f'if(original.{n}.dpram1.out2 !== diagnostic.{n}.dpram1.out2)begin if(ramdiff{i}==0)$display("RAM_FIRST_DIFFERENCE instance={n} cycle=%0d original=%h diagnostic=%h",cycle,original.{n}.dpram1.out2,diagnostic.{n}.dpram1.out2);ramdiff{i}=ramdiff{i}+1;end');ram_summary.append(f'$display("RAM_OUTPUT_SUMMARY instance={n} differing_cycles=%0d",ramdiff{i});')
 inputpins='.reset(reset),.clk(clk),.constants(constants),.read_constants(read_constants),.inc_result(inc_result)';stateidx=list(outputs).index('r_state');counteridx=list(outputs).index('r_counter');tb='''`timescale 1ns/1ps
module tb;
reg reset=1,clk=0,read_constants=0,inc_result=0;reg[31:0]constants=1;integer cycle,threshold;reg[15:0]state_seen=0;
'''+ '\n'.join(decl)+f'\nmcml original({inputpins},'+','.join(portsA)+');\n'+f'mcml_rc_orderdiag diagnostic({inputpins},'+','.join(portsB)+');\n'+f'''initial begin
#5;clk=1;#1;#4;clk=0;#5;clk=1;#1;#4;clk=0;reset=0;
for(cycle=0;cycle<90000;cycle=cycle+1)begin
case(a{stateidx})1:threshold=104;2,3:threshold=640;4,5:threshold=5120;default:threshold=0;endcase
read_constants=threshold>0 && a{counteridx}<threshold;
#5;clk=1;#1;
if(^a{stateidx} !== 1'bx && !state_seen[a{stateidx}])begin state_seen[a{stateidx}]=1;$display("TOP_STATE_REACHED state=%0d cycle=%0d",a{stateidx},cycle);end
'''+ '\n'.join(comparisons+monitors)+'''\n#4;clk=0;
end
'''+ '\n'.join(summary+ram_summary)+'''\n$display("TOP_ORDER_DIAGNOSTIC_COMPLETE cycles=90000 states=%h",state_seen);$finish;
end endmodule\n''';(D/'tb.v').write_text(tb);(D/'run.tcl').write_text('run all\nquit\n');rows=[]
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 for cmd in [[str(BIN/'xvlog'),'--relax',str(LIB),str(D/'diagnostic_ram.v'),str(SRC),str(D/'diagnostic_mcml.v'),str(D/'tb.v')],[str(BIN/'xelab'),'tb','-s','order_top'],[str(BIN/'xsim'),'order_top','-tclbatch',str(D/'run.tcl')]]:
  with (D/(Path(cmd[0]).name+'.stdout.log')).open('w') as log:code=subprocess.call(cmd,cwd=D,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  rows.append({'command':cmd,'exit_code':code});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(Path(cmd[0]).name,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
