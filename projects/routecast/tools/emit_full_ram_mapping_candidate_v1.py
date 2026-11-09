"""Emit complete collected Full candidate with explicit delayed-write RAM wrappers.

Native macros are black boxes here: structural acceptance is not functional proof.
"""
import hashlib
import json
import subprocess
from pathlib import Path

R=Path(__file__).resolve().parents[1]
E=R/'experiments'
D=E/'full_ram_mapping_candidate_v1_2026-10-09'
D.mkdir(exist_ok=False)
source=E/'vexriscv_full_memory_candidate_v2_2026-10-09/design.json'
planfile=E/'full_ram_lane_plan_v1_2026-10-09/plan.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
plan=json.loads(planfile.read_text())
assert sha(source)==plan['source_sha256']
design=json.loads(source.read_text())
cells=design['modules']['VexRiscvFull']['cells']
rtl=['''(* blackbox *) module dual_port_ram #(parameter ADDR_WIDTH=10,DATA_WIDTH=20)
(input clk,we1,we2,input [ADDR_WIDTH-1:0] addr1,addr2,
input [DATA_WIDTH-1:0] data1,data2,output [DATA_WIDTH-1:0] out1,out2);
endmodule
module rc_delayed_slice(input clk,we,re,input [9:0] wa,ra,input [19:0] data,output [19:0] q);
reg pw=0,er=0,hit;
reg [9:0] pa; reg [19:0] pd,fwd,held; wire [19:0] raw,unused;
dual_port_ram #(.ADDR_WIDTH(10),.DATA_WIDTH(20)) ram
(.clk(clk),.we1(pw),.we2(1'b0),.addr1(pa),.addr2(ra),.data1(pd),.data2(20'b0),.out1(unused),.out2(raw));
assign q=er ? (hit ? fwd : raw) : held;
always @(posedge clk) begin
held<=q; er<=re; hit<=pw && pa==ra; fwd<=pd;
pw<=we; pa<=wa; pd<=data;
end
endmodule
''']
for i,row in enumerate(plan['memories']):
    name=row['name']; old=cells[name]; p=old['parameters']; c=old['connections']
    val=lambda k:int(p[k],2)
    w,ab,nr=val('WIDTH'),val('ABITS'),val('RD_PORTS')
    assert val('OFFSET')==0 and val('SIZE')==2**ab
    assert val('RD_CLK_ENABLE')==(1<<nr)-1 and val('WR_CLK_ENABLE')==1
    assert val('RD_CLK_POLARITY')==(1<<nr)-1 and val('WR_CLK_POLARITY')==1
    assert c['RD_ARST']==['0']*nr and c['RD_SRST']==['0']*nr
    assert set(p['INIT'])=={'x'} and set(p['RD_INIT_VALUE'])=={'x'}
    typ=f'rc_full_memory_{i}'
    rtl.append(f'module {typ}(input CLK,WE,input [{ab-1}:0] WA,input [{w-1}:0] WD,input [{nr*ab-1}:0] RA,input [{nr-1}:0] RE,output [{nr*w-1}:0] Q);\n')
    for j,s in enumerate(row['slices']):
        a,b,rd=s['start'],s['stop'],s['read_port']; n=b-a
        wa='WA' if ab==10 else f"{{{10-ab}'b0,WA}}"
        ra=f'RA[{rd*ab+ab-1}:{rd*ab}]'
        if ab<10:ra=f"{{{10-ab}'b0,{ra}}}"
        data=f'WD[{b-1}:{a}]'
        if n<20:data=f"{{{20-n}'b0,{data}}}"
        rtl.append(f'wire [19:0] q{j}; rc_delayed_slice s{j}(.clk(CLK),.we(WE),.re(RE[{rd}]),.wa({wa}),.ra({ra}),.data({data}),.q(q{j}));\nassign Q[{rd*w+b-1}:{rd*w+a}]=q{j}[{n-1}:0];\n')
    rtl.append('endmodule\n')
    connections=dict(CLK=c['WR_CLK'],WE=[c['WR_EN'][0]],WA=c['WR_ADDR'],WD=c['WR_DATA'],RA=c['RD_ADDR'],RE=c['RD_EN'],Q=c['RD_DATA'])
    cells[name]=dict(hide_name=0,type=typ,parameters={},attributes=old['attributes'],
        port_directions={k:('output' if k=='Q' else 'input') for k in connections},connections=connections)
(D/'candidate.json').write_text(json.dumps(design)+'\n')
(D/'wrappers.v').write_text(''.join(rtl))
oldprotocol=json.loads((E/'vexriscv_family_flattened_inventory_v1_2026-10-09/protocol.json').read_text())
y=Path(next(p for p in oldprotocol['bindings'] if p.endswith('/bin/yosys')))
assert sha(y)==oldprotocol['bindings'][str(y)]
script='read_json candidate.json\nread_verilog wrappers.v\nhierarchy -check -top VexRiscvFull\nproc\nflatten\nopt_clean\ncheck -assert\nwrite_json structural.json\n'
(D/'prepare.ys').write_text(script)
bindings={str(p):sha(p) for p in (Path(__file__),source,planfile,y,D/'candidate.json',D/'wrappers.v',D/'prepare.ys')}
command=[str(y),'-s','prepare.ys']
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,command=command,timeout_s=120,
    scope='Complete Full collected candidate, all nine memories replaced; native dual_port_ram blackbox. Structural check only; no macro semantics, Full equivalence, packed input or prediction admission.'),indent=2)+'\n')
with (D/'prepare.log').open('x') as log:
    try:code=subprocess.run(command,cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
    except subprocess.TimeoutExpired:code='TIMEOUT'
receipt=dict(exit_code=code,bindings=bindings,admitted_for_prediction=False)
if code==0:
    out=json.loads((D/'structural.json').read_text())['modules']['VexRiscvFull']
    macros=[c for c in out['cells'].values() if c['type']=='dual_port_ram']
    assert len(macros)==plan['macro_count']
    assert not any(c['type']=='$mem_v2' for c in out['cells'].values())
    assert out['ports']==design['modules']['VexRiscvFull']['ports']
    receipt.update(native_macro_instances=len(macros),top_ports_preserved=True,structural_pass=True)
receipt['files']={str(p):sha(p) for p in D.iterdir() if p.is_file()}
(D/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(code,receipt.get('native_macro_instances'),flush=True)
