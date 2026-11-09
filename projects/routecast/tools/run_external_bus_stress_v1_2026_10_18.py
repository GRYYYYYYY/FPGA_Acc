"""Predeclared deterministic finite bus stress, original RTL versus mapped model."""
import sys,json,subprocess,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 prior=R/'experiments/prospective_external_family_mapped_differential_v2_2026-10-18';proof=prior/'receipt.json';r=json.loads(proof.read_text());assert r['passed']
 for p,h in r['files'].items():assert sha(p)==h
 src=R/'experiments/prospective_external_family_source_v2_2026-10-18/upstream/src/rtl';rtl=sorted(src.glob('*.v'));mapped=prior/'mapped.v';runtime=R/'experiments/prospective_external_family_sim_runtime_v1_2026-10-18/root/usr';iv=runtime/'bin/iverilog';vvp=runtime/'bin/vvp';lib=runtime/'lib/x86_64-linux-gnu/ivl';out=R/'experiments/prospective_external_family_bus_stress_v1_2026-10-18';out.mkdir(exist_ok=False);bindings={str(p):sha(p) for p in [Path(__file__),proof,mapped,iv,vvp,*rtl]}
 ports=['.clk(clk)','.reset_n(reset_n)','.cs(cs)','.we(we)']
 for name,width,signal in [('addr',8,'addr'),('write_data',32,'data'),('read_data',32,'gate_data')]:ports.extend('.\\'+name+'['+str(i)+'] ('+signal+'['+str(i)+'])' for i in range(width))
 harness='''module stress;
reg clk=0; always #5 clk=~clk;
reg reset_n=0,cs=0,we=0;reg [7:0] addr=0;reg [31:0] data=0;
wire [31:0] source_data,gate_data;
chacha source(.clk(clk),.reset_n(reset_n),.cs(cs),.we(we),.addr(addr),.write_data(data),.read_data(source_data));
'''+ 'mapped_chacha gate('+','.join(ports)+');\n'+'''
integer sample=0;integer phase;integer step;reg [31:0] state;integer addresses[0:255];integer writes=0;integer reads=0;
initial begin
for(step=0;step<256;step=step+1) addresses[step]=0;
for(phase=0;phase<3;phase=phase+1) begin
state=32'h10203041+phase*32'h112233;
reset_n=0;cs=0;we=0;
repeat(4) @(negedge clk);
for(step=0;step<1024;step=step+1) begin
state=state*32'd1664525+32'd1013904223;
reset_n= ((step%257)>=2);cs=state[31];we=state[30];addr=step[7:0];data=state;
addresses[addr]=addresses[addr]+1;
if(cs&&we) writes=writes+1;if(cs&&!we) reads=reads+1;
@(posedge clk);#1;
if ((source_data !== gate_data) || (^source_data === 1'bx) || (^gate_data === 1'bx)) $fatal(1,"STRESS_FAIL phase=%0d step=%0d addr=%h source=%h gate=%h",phase,step,addr,source_data,gate_data);
sample=sample+1;@(negedge clk);
end
end
for(step=0;step<256;step=step+1) if(addresses[step]!=12) $fatal(1,"ADDRESS_COVERAGE_FAIL");
$display("STRESS_PASS samples=%0d writes=%0d reads=%0d addresses=256",sample,writes,reads);$finish;
end
endmodule
'''
 hp=out/'stress.sv';hp.write_text(harness);(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,harness_sha256=sha(hp),samples=3072,seeds=[0x10203041+i*0x112233 for i in range(3)],address_schedule='all256addresses repeated4times per seed',reset_schedule='4initialclockcycles per seed then low for first2steps of each257step period',scope='Arbitrary defined raw bus transactions, including potentially unsupported register values. Finite differential stress only, not cryptographic correctness specification or RC placement/routing labels.'),indent=2))
 cmd=[str(iv),'-B',str(lib),'-g2012','-s','stress','-o',str(out/'sim.vvp'),*[str(p) for p in rtl],str(mapped),str(hp)]
 with (out/'compile.log').open('x') as log:code=subprocess.call(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT)
 assert code==0
 with (out/'simulation.log').open('x') as log:
  child=subprocess.Popen([str(vvp),'-M',str(lib),str(out/'sim.vvp')],cwd=out,stdout=log,stderr=subprocess.STDOUT);(out/'live_process.json').write_text(json.dumps(dict(pid=child.pid)));print('BUS STRESS CHILD',child.pid,flush=True);code=child.wait()
 text=(out/'simulation.log').read_text();match=re.search(r'STRESS_PASS samples=(\d+) writes=(\d+) reads=(\d+) addresses=256',text);passed=code==0 and match is not None and int(match[1])==3072
 for p,h in bindings.items():assert sha(p)==h
 files={str(p):sha(p) for p in out.iterdir() if p.is_file()}
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='finite_independent_bus_stress_pass' if passed else 'finite_bus_stress_failed',bindings=bindings,files=files,exit_code=code,passed=passed,counts=match.groups() if match else None,scope='Finite deterministic comparison to techmapped simulation representation; original indexed-LUT X failure remains. No full HDL/timing, family admission, forecast quality or utility conclusion.'),f,indent=2)
 print('BUS STRESS TERMINAL',code,passed,flush=True)
if __name__=='__main__':main()
