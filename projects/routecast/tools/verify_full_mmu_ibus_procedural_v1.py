"""Extract original procedural MMU cases for a local XSIM four-state invariant check."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/full_mmu_ibus_procedural_v1_2026-10-09';D.mkdir(exist_ok=True)
f=R/'experiments/full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';lines=f.read_text().splitlines()
state='\n'.join(lines[5742:5778]);assert state.strip().startswith('case(') and state.strip().endswith('endcase')
select='\n'.join(lines[6045:6062]);assert select.strip().startswith('case(') and select.strip().endswith('endcase')
params='\n'.join(lines[65:70])
v='''module tb;
reg clk=0,reset=0;reg [2:0] MmuPlugin_shared_state_1;reg [1:0] MmuPlugin_shared_portSortedOh;
reg MmuPlugin_dBusAccess_cmd_ready,MmuPlugin_shared_dBusRspStaged_valid,when_MmuPlugin_l244,MmuPlugin_shared_dBusRspStaged_payload_redo;
reg dbus_request;wire [1:0] raw={dbus_request,1'b0};wire [1:0] rev={raw[0],raw[1]};wire [1:0] onehot=rev & ~(rev-2'b01);
wire [1:0] MmuPlugin_shared_refills={onehot[0],onehot[1]};wire when_MmuPlugin_l218=|MmuPlugin_shared_refills;
reg [9:0] MmuPlugin_shared_vpn_1,MmuPlugin_shared_vpn_0;wire [31:0] _zz_MmuPlugin_shared_vpn_0=32'bx;
wire busy=(MmuPlugin_shared_state_1!=0)&&MmuPlugin_shared_portSortedOh[0];
'''+params+'\nalways @(posedge clk or posedge reset) begin if(reset) MmuPlugin_shared_state_1<=MmuPlugin_shared_State_IDLE;else begin\n'+state+'\nend end\nalways @(posedge clk) begin\n'+select+'''\nend
function ternary_value; input integer k;begin case(k) 0:ternary_value=0;1:ternary_value=1;default:ternary_value=1'bx;endcase end endfunction
integer s,i,j,k,count=0;
initial begin
reset=1;#1;if(busy!==0)$fatal(1,"reset base");reset=0;
for(s=0;s<5;s=s+1) for(i=0;i<243;i=i+1) begin
clk=0;MmuPlugin_shared_state_1=s;MmuPlugin_shared_portSortedOh=(s==0)?2'bxx:2'bx0;
k=i;dbus_request=ternary_value(k%3);k=k/3;MmuPlugin_dBusAccess_cmd_ready=ternary_value(k%3);k=k/3;
MmuPlugin_shared_dBusRspStaged_valid=ternary_value(k%3);k=k/3;when_MmuPlugin_l244=ternary_value(k%3);k=k/3;MmuPlugin_shared_dBusRspStaged_payload_redo=ternary_value(k%3);
#1;if(MmuPlugin_shared_refills[0]!==0 || busy!==0)$fatal(1,"precondition");
clk=1;#1;if(busy!==0)$fatal(1,"invariant state=%d controls=%d",s,i);count=count+1;
end
$display("PROCEDURAL_IBUS_PASS cases=%0d",count);$finish;
end
endmodule
'''
(D/'tb.v').write_text(v)
(D/'extraction.json').write_text(json.dumps({'source_sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'state_case':state,'selector_case':select,'tb_sha256':hashlib.sha256(v.encode()).hexdigest(),'scope':'Original extracted procedural state/selector cases, reset base and 1215 ternary one-step ternary_valueals. IBus raw request0 premise supplied by separate mask proof; no full replay or export event correspondence.'},indent=2)+'\n')
print(D)
