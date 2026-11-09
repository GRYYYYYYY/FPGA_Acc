"""Original IBus procedural masking and settled logical-ready four-state trials."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_ibus_mask_ready_fourstate_v1_2026-10-09';D.mkdir(exist_ok=True)
f=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';ls=f.read_text().splitlines()
mask='\n'.join(ls[4116:4128]);halt='\n'.join(ls[3614:3623]);assert mask.strip().startswith('always') and halt.strip().startswith('always')
v='''module tb;
wire [1:0] CsrPlugin_privilege=2'b11;
reg [31:0] IBusCachedPlugin_mmuBus_cmd_0_virtualAddress;
reg IBusCachedPlugin_mmuBus_cmd_0_bypassTranslation,MmuPlugin_satp_mode,MmuPlugin_status_mprv;
wire when_MmuPlugin_l126,when_MmuPlugin_l127;reg MmuPlugin_ports_0_requireMmuLockupCalc;
reg cmdvalid,dirty,cachehit;
wire rawrequest=((cmdvalid && MmuPlugin_ports_0_requireMmuLockupCalc)&&!dirty)&&!cachehit;
reg IBusCachedPlugin_mmuBus_busy,IBusCachedPlugin_iBusRsp_stages_1_output_ready;
reg IBusCachedPlugin_iBusRsp_stages_1_halt;
wire _zz_IBusCachedPlugin_iBusRsp_stages_1_input_ready,IBusCachedPlugin_iBusRsp_stages_1_input_ready;
'''+mask+'\n'+halt+'''
function tv;input integer n;begin case(n)0:tv=0;1:tv=1;default:tv=1'bx;endcase end endfunction
integer i,k,j,count=0;
initial begin
IBusCachedPlugin_mmuBus_busy=0;IBusCachedPlugin_iBusRsp_stages_1_output_ready=0;
for(i=0;i<59049;i=i+1)begin
k=i;for(j=28;j<32;j=j+1)begin IBusCachedPlugin_mmuBus_cmd_0_virtualAddress[j]=tv(k%3);k=k/3;end
IBusCachedPlugin_mmuBus_cmd_0_bypassTranslation=tv(k%3);k=k/3;MmuPlugin_satp_mode=tv(k%3);k=k/3;
MmuPlugin_status_mprv=tv(k%3);k=k/3;cmdvalid=tv(k%3);k=k/3;dirty=tv(k%3);k=k/3;cachehit=tv(k%3);
#1;if(MmuPlugin_ports_0_requireMmuLockupCalc!==0 || rawrequest!==0)$fatal(1,"mask %d",i);count=count+1;
end
for(i=0;i<3;i=i+1)begin IBusCachedPlugin_iBusRsp_stages_1_output_ready=tv(i);#1;
if(IBusCachedPlugin_iBusRsp_stages_1_input_ready!==tv(i))$fatal(1,"ready");end
IBusCachedPlugin_iBusRsp_stages_1_output_ready=1'bz;#1;
if(IBusCachedPlugin_iBusRsp_stages_1_input_ready!==1'bx)$fatal(1,"Z distinction");
$display("MASK_READY_PASS cases=%0d ready=3 Z_distinction=1",count);$finish;
end endmodule
'''
(D/'tb.v').write_text(v)
(D/'extraction.json').write_text(json.dumps({'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'mask':mask,'halt_ready':halt,'scope':'Original extracted fixed-privilege IBus lookup masking:59049 ternary inputs; source settled ready equals output-ready for0/1/X under busy0, but Z becomesX. Raw request reproduces actual source AND expression. Does not establish source/native output-ready histories or full memory/event relation.'},indent=2)+'\n')
print(D)
