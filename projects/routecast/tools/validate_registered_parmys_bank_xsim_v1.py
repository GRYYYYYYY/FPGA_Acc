"""Independent HDL replay of actual mapped JSON with original functional RAM."""
import hashlib,json,os,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/parmys_registered_bank_select_v1_2026-10-21';D=R/'experiments/parmys_registered_bank_xsim_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';B=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);rows=[];lib=V/'vtr_flow/primitives.v';protocol={'scope':'Independent XSim concrete event trace, actual mapped gates and original functional RAM contract. No source-family equivalence or physical architecture proof. No initial memory values assigned. Both read ports checked after explicit writes; we2=0, cross-port write/read same-address collisions excluded.', 'bindings':{str(p):sha(p) for p in [Path(__file__),lib,P/'dp13x32/repaired.json',P/'dp16x36/repaired.json']}};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 for name,a,w in [('dp13x32',13,32),('dp16x36',16,36)]:
  f=D/name;f.mkdir();m=json.loads((P/name/'repaired.json').read_text())['modules']['probe'];ports=m['ports'];cells=m['cells'];nets=sorted({b for c in cells.values() for bits in c['connections'].values() for b in bits if isinstance(b,int)}|{b for p in ports.values() for b in p['bits'] if isinstance(b,int)})
  def bit(b):return 'n'+str(b) if isinstance(b,int) else "1'b"+b
  def vec(xs):return '{'+','.join(bit(b) for b in reversed(xs))+'}'
  s=[f'module mapped_probe(input clk,input [{a-1}:0] addr1,addr2,input [{w-1}:0] data1,input we1,output [{w-1}:0] out1,out2);','wire '+','.join('n'+str(b) for b in nets)+';']
  for k,p in ports.items():
   base,sep,idx=k.partition('~');external=base+('['+idx+']' if sep else '');internal=vec(p['bits']);s.append(f'assign {internal if p["direction"]=="input" else external} = {external if p["direction"]=="input" else internal};')
  for i,c in enumerate(cells.values()):
   z=c['connections'];t=c['type']
   if t=='dual_port_ram':s.append('dual_port_ram #(.ADDR_WIDTH(11),.DATA_WIDTH(1)) ram'+str(i)+'('+','.join('.'+k+'('+vec(v)+')' for k,v in z.items())+');')
   elif t=='$dff':
    assert z['CLK']==ports['clk']['bits'] and c['parameters']['CLK_POLARITY']=='1';s.append('reg ['+str(len(z['Q'])-1)+':0] bank_q; always @(posedge clk) bank_q <= '+vec(z['D'])+'; assign '+vec(z['Q'])+' = bank_q;')
   else:
    assert t in ['$and','$reduce_or','$reduce_and','$logic_not'];expr=(vec(z['A'])+' & '+vec(z['B'])) if t=='$and' else {'$reduce_or':'|','$reduce_and':'&','$logic_not':'!'}[t]+vec(z['A']);s.append('assign '+vec(z['Y'])+' = '+expr+';')
  s.append('endmodule');(f/'mapped.v').write_text('\n'.join(s)+'\n')
  tb=f'''`timescale 1ns/1ps
module tb;
reg clk=0; reg [{a-1}:0] addr1=0,addr2=17; reg [{w-1}:0] data1=0;reg we1=0;
wire [{w-1}:0] refout,mappedout,refout2,mappedout2;
reg [{w-1}:0] hold1,hold2;integer i,j;reg [31:0] rng=32'h5a179d03;
dual_port_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) refdut(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.data2({w}'b0),.we1(we1),.we2(1'b0),.out1(refout),.out2(refout2));
mapped_probe dut(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.we1(we1),.out1(mappedout),.out2(mappedout2));
task edgecheck;input [{w-1}:0] expected;begin #5;clk=1;#1;if(refout !== expected || mappedout !== expected) $fatal(1,"edge mismatch");$display("EDGE_MATCH ref=%h mapped=%h",refout,mappedout);#4;clk=0;end endtask
initial begin
we1=1;addr1=0;data1=1;edgecheck(1);
addr1=1;data1=0;edgecheck(0);
we1=0;addr1=0;edgecheck(1);
#2;addr1=1;#1;
if(refout !== {w}'d1 || mappedout !== {w}'d1) $fatal(1,"hold repair failed");
$display("ORIGINAL_COUNTEREXAMPLE_REPAIRED ref=%h mapped=%h clk=%b",refout,mappedout,clk);
// Initialize both rows of every bank through public writes, not initial state assumptions.
for(i=0;i<{1<<(a-10)};i=i+1) begin
clk=0;addr1=i;addr2=17;data1=i*37+5;we1=1;#5;clk=1;#1;if(refout !== mappedout) $fatal(1,"initializing write mismatch");#4;clk=0;
end
for(j=0;j<512;j=j+1) begin
rng=rng*1664525+1013904223;addr1=rng%{1<<(a-10)};
rng=rng*1664525+1013904223;addr2=rng%{1<<(a-10)};
if(addr2==addr1)addr2=(addr1+1)%{1<<(a-10)};
data1=rng^(rng<<13);we1=j%3==0;
#5;clk=1;#1;
if(refout !== mappedout || refout2 !== mappedout2) $fatal(1,"read/write mismatch j=%d",j);
hold1=refout;hold2=refout2;#4;clk=0;
addr1=addr1^1;addr2=addr2^1;#1;
if(refout !== hold1 || mappedout !== hold1 || refout2 !== hold2 || mappedout2 !== hold2) $fatal(1,"between-edge hold mismatch");
end
$display("REGISTERED_BANK_TRACE_PASS cycles=512 banks={1<<(a-11)}");$finish;
end
endmodule
''';(f/'tb.v').write_text(tb);(f/'run.tcl').write_text('run all\nquit\n');stages=[]
  for cmd in [[str(B/'xvlog'),str(lib),str(f/'mapped.v'),str(f/'tb.v')],[str(B/'xelab'),'tb','-s','read_hold'],[str(B/'xsim'),'read_hold','-tclbatch',str(f/'run.tcl')]]:
   start=time.monotonic()
   with (f/(Path(cmd[0]).name+'.stdout.log')).open('w') as out:code=subprocess.call(cmd,cwd=f,stdout=out,stderr=subprocess.STDOUT)
   stages.append({'command':cmd,'exit_code':code,'seconds':time.monotonic()-start});print(name,Path(cmd[0]).name,code,flush=True)
   if code:break
  log=f/'xsim.log';confirmed=log.exists() and 'REGISTERED_BANK_TRACE_PASS cycles=512' in log.read_text();rows.append({'case':name,'stages':stages,'counterexample_confirmed':confirmed});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
