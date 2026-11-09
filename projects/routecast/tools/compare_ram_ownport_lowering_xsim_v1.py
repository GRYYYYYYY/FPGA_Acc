"""Paired original RTL and pinned raw standard-flag IR, collision-free port2."""
import json,hashlib,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'ram_mapping_semantics_v1_2026-10-20/standard_nomem2reg_disabled_port/constant_zero_we2';D=E/'ram_ownport_lowering_xsim_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';B=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);m=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(m['yosys_binary']);lib=V/'vtr_flow/primitives.v';runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');protocol={'scope':'Same tiny source as pinned raw frontend IR. Original functional model versus memory_map-exported raw IR in independent HDL simulator. Port2 reads address1; writes address0, so no cross-port collision. No memory initialized except through public writes. Raw elaboration/proc path is not complete standard Parmys synthesis flow.','bindings':{str(p):sha(p) for p in [Path(__file__),P/'probe.v',P/'proc.json',lib,binary,runtime]}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');ys=D/'export.ys';ys.write_text(f'read_json {P/"proc.json"}\nhierarchy -top probe\nmemory -nomap\nmemory_map\nopt_clean\ncheck -assert\nrename probe lowered_probe\nwrite_verilog -noattr {D/"lowered.v"}\n')
 with (D/'export.log').open('w') as out:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=D,env=env,stdout=out,stderr=subprocess.STDOUT)
 assert code==0
 (D/'tb.v').write_text('''`timescale 1ns/1ps
module tb;
reg clk=0;reg [1:0]data1=1;wire [1:0] rtl,lowered;
probe original(.clk(clk),.addr1(1'b0),.addr2(1'b1),.data1(data1),.data2(2'b0),.we1(1'b1),.we2(1'b0),.out1(rtl),.out2());
lowered_probe lowered_ir(.clk(clk),.addr1(1'b0),.addr2(1'b1),.data1(data1),.data2(2'b0),.we1(1'b1),.we2(1'b0),.out1(lowered),.out2());
initial begin
#5;clk=1;#1;if(rtl !== 2'd1)$fatal(1,"first source write");#4;clk=0;
data1=2;#5;clk=1;#1;
if(rtl !== 2'd2 || lowered !== 2'd1)$fatal(1,"expected own-port mismatch absent");
$display("OWNPORT_LOWERING_MISMATCH_CONFIRMED original=%d lowered=%d crossport_collision=0",rtl,lowered);$finish;
end
endmodule
''');(D/'run.tcl').write_text('run all\nquit\n');rows=[]
 for cmd in [[str(B/'xvlog'),str(lib),str(P/'probe.v'),str(D/'lowered.v'),str(D/'tb.v')],[str(B/'xelab'),'tb','-s','ownport'],[str(B/'xsim'),'ownport','-tclbatch',str(D/'run.tcl')]]:
  with (D/(Path(cmd[0]).name+'.stdout.log')).open('w') as out:code=subprocess.call(cmd,cwd=D,stdout=out,stderr=subprocess.STDOUT)
  rows.append({'command':cmd,'exit_code':code});print(Path(cmd[0]).name,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
