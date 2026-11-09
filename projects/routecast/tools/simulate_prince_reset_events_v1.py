"""Actual pinned Icarus scheduling probes; mismatch is a retained outcome."""
import json,subprocess,re,time
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_reset_event_sim_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);runtime=E/'prospective_external_family_sim_runtime_v1_2026-10-18';pkg=runtime/'iverilog_11.0-1.1_amd64.deb';assert sha(pkg)=='56b2b91e23f51c571b8cf43ef2df3a137a1bf4b6bcbff0fa3463b5b89403a852';usr=runtime/'root/usr';iv=usr/'bin/iverilog';vvp=usr/'bin/vvp';lib=usr/'lib/x86_64-linux-gnu/ivl';sim=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/share/yosys/simcells.v';tb=D/'events_tb.v'
 tb.write_text(r'''`timescale 1ns/1ps
module events_tb;
reg C,R,D,seed;
wire RI=~R;
wire g0,g1,n0,n1;
\$_DFF_PN0_ G0(.C(C),.R(R),.D(D),.Q(g0));
\$_DFF_PN1_ G1(.C(C),.R(R),.D(D),.Q(g1));
\$_DFF_PP0_ N0(.C(C),.R(RI),.D(D),.Q(n0));
\$_DFF_PP1_ N1(.C(C),.R(RI),.D(D),.Q(n1));
integer mode,c0,c1,r0,r1,di,qi;
integer checked[0:5]; integer mismatch[0:5];
function value(input integer i);
begin case(i) 0:value=1'b0;1:value=1'b1;2:value=1'bx;3:value=1'bz;endcase end
endfunction
initial begin
for(mode=0;mode<6;mode=mode+1) begin
checked[mode]=0; mismatch[mode]=0;
for(c0=0;c0<4;c0=c0+1) for(c1=0;c1<4;c1=c1+1)
for(r0=0;r0<4;r0=r0+1) for(r1=0;r1<4;r1=r1+1)
for(di=0;di<4;di=di+1) for(qi=0;qi<4;qi=qi+1) begin
C=value(c0);R=value(r0);D=value(di);seed=value(qi);#2;
force G0.Q=seed;force G1.Q=seed;force N0.Q=seed;force N1.Q=seed;
#1;release G0.Q;release G1.Q;release N0.Q;release N1.Q;
case(mode)
0:begin {C,R}={value(c1),value(r1)};end
1:begin R=value(r1);C=value(c1);end
2:begin C=value(c1);R=value(r1);end
3:begin C<=value(c1);R<=value(r1);end
4:begin R=value(r1);#0;C=value(c1);end
5:begin C=value(c1);#0;R=value(r1);end
endcase
#1;checked[mode]=checked[mode]+2;
if(g0 !== n0) begin
if(mismatch[mode]<8) $display("DIFF mode=%0d c=%b->%b r=%b->%b D=%b seed=%b reset=0 gold=%b normalized=%b",mode,value(c0),value(c1),value(r0),value(r1),D,seed,g0,n0);
mismatch[mode]=mismatch[mode]+1;end
if(g1 !== n1) begin
if(mismatch[mode]<8) $display("DIFF mode=%0d c=%b->%b r=%b->%b D=%b seed=%b reset=1 gold=%b normalized=%b",mode,value(c0),value(c1),value(r0),value(r1),D,seed,g1,n1);
mismatch[mode]=mismatch[mode]+1;end
end
$display("MODE_RESULT %0d %0d %0d",mode,checked[mode],mismatch[mode]);
end
$display("EVENT_PROBE_COMPLETE");$finish;
end
endmodule
''');image=D/'events.vvp';compile_command=[str(iv),'-B',str(lib),'-g2012','-s','events_tb','-o',str(image),str(sim),str(tb)];simulation_command=[str(vvp),'-M',str(lib),str(image)];files=[Path(__file__),pkg,iv,vvp,sim,tb,E/'prince_reset_polarity_verification_v1_2026-10-20/verification.json',*[p for p in lib.iterdir() if p.is_file()]];bindings={str(p):sha(p) for p in files};protocol={'status':'FROZEN_EXHAUSTIVE_PRIMITIVE_FOUR_VALUE_SCHEDULING_PROBE','compile_command':compile_command,'simulation_command':simulation_command,'modes':['simultaneous_concatenated_blocking','reset_then_clock_same_active_process','clock_then_reset_same_active_process','simultaneous_nonblocking','reset_then_delta_then_clock','clock_then_delta_then_reset'],'cases':'All4^6 clock/reset old/new,D,forced shared priorQ; both reset constants. Force/release sets shared prior state for isolated event testing, not a claim of full-circuit reachable initial state.','scope':'Exact pinned Icarus/simcells finite scheduler fixtures, not universal scheduler/physical timing/full source equivalence. Mismatches retained, no retry/filtering/timing assumptions for label admission.','bindings':bindings};(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');tick=time.perf_counter()
 with (D/'compile.log').open('x') as log:code=subprocess.call(compile_command,stdout=log,stderr=subprocess.STDOUT)
 assert code==0
 with (D/'simulation.log').open('x') as log:code=subprocess.call(simulation_command,stdout=log,stderr=subprocess.STDOUT)
 text=(D/'simulation.log').read_text();assert code==0 and 'EVENT_PROBE_COMPLETE' in text;rows=[{'mode':int(m),'comparisons':int(n),'mismatches':int(b)} for m,n,b in re.findall(r'MODE_RESULT (\d+) (\d+) (\d+)',text)];assert len(rows)==6 and all(r['comparisons']==8192 for r in rows);assert all(sha(p)==h for p,h in bindings.items());receipt={'status':'ACTUAL_EVENT_PROBE_COMPLETED_MISMATCHES_RETAINED','rows':rows,'all_modes_equal':all(r['mismatches']==0 for r in rows),'component_seconds':time.perf_counter()-tick,'native_labels_generated':False,'bindings':{str(p):sha(p) for p in [D/'protocol.json',D/'compile.log',D/'simulation.log',image]},'scope':protocol['scope']};(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PRINCE_ACTUAL_EVENT_PROBE',rows,flush=True)
if __name__=='__main__':main()
