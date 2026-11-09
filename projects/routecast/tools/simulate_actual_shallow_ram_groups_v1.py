"""Extract exact completed physical RAM lanes into local behavioral fixtures."""
import json,hashlib,re,subprocess
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'actual_shallow_ram_xsim_v1_2026-10-21';P=E/'shallow_ram_address_completion_v1_2026-10-21';B=E/'parmys_source_provenance_replay_v1_2026-10-21';V=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';BIN=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);prov=json.loads((B/'verification_v1.json').read_text());library=V/'vtr_flow/primitives.v';paths=[P/r['source']/'candidate.json' for r in prov['rows']];(D/'protocol.json').write_text(json.dumps({'scope':'All12 actual completed shallow groups as local fixtures. Exact physical macro pin shapes/constants/low-address/lane wiring retained under input renaming; upstream source sequential/control logic abstracted.9writable groups public-write-initialize all rows,512noncollision cycles plus between-edge holds.3read-only groups retain we=0 and uninitialized memories, no content-equivalence claim. Original functional word primitive reference, no modified RTL library.','bindings':{str(p):sha(p) for p in [Path(__file__),library,B/'verification_v1.json',*paths]}},indent=2)+'\n');texts=[];receipts=[];index=0
 for row,path in zip(prov['rows'],paths):
  obj=json.loads(path.read_text())['modules'][row['source']];aliases=defaultdict(list)
  for n,v in obj['netnames'].items():
   for bit in v['bits']:aliases[bit].append(n)
  for g in row['groups']:
   if g['address_bits']>=11:continue
   a,w=g['address_bits'],g['data_bits'];physical=[obj['cells'][n] for n in g['descendant_cells']];dp=physical[0]['type']=='dual_port_ram';common=physical[0]['connections'];lanes={}
   for name in g['descendant_cells']:
    c=obj['cells'][name];out='out1' if dp else 'out';matches={int(match.group(1)) for bit in c['connections'][out] for alias in aliases[bit] if (match:=re.match(re.escape(g['mapper_memory_root'])+r'-(\d+)\^out',alias))};assert len(matches)==1;lane=next(iter(matches));assert lane not in lanes;lanes[lane]=(name,c)
   assert set(lanes)==set(range(w));connections={};node_map={};constants=[]
   def bind(bits,label):
    for i,b in enumerate(bits):
     if isinstance(b,int):node_map.setdefault(b,label+(f'[{i}]' if len(bits)>1 else ''))
   bind(common['clk'],'clk')
   for port in ['addr1','addr2'] if dp else ['addr']:bind(common[port][:a],port)
   we='we1' if dp else 'we';bind(common[we],'we');data='data1' if dp else 'data'
   for i,(_,c) in lanes.items():
    b=c['connections'][data][0]
    if isinstance(b,int):node_map.setdefault(b,f'data[{i}]')
   def bit(b):return node_map[b] if isinstance(b,int) else "1'b"+b
   def vec(bs):return '{'+','.join(bit(b) for b in reversed(bs))+'}'
   effective=[bit(lanes[i][1]['connections'][data][0]) for i in range(w)];we_expr=vec(common[we]);ro=common[we]==['0'];header=f'''`timescale 1ns/1ps
module checker{index}(output reg done=0);
reg clk=0;reg [{a-1}:0] addr1=0,addr2=0;wire [{a-1}:0] addr=addr1;reg [{w-1}:0] data=0;reg we=0;wire [{w-1}:0] effective_data={{{','.join(reversed(effective))}}};wire [{w-1}:0] ref1,ref2,phy1,phy2;reg [{w-1}:0] held1,held2;integer i,j;reg [31:0] rng=32'h67a113bd;
''';texts.append(header)
   if dp:texts.append(f'dual_port_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) reference(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(effective_data),.data2({w}\'b0),.we1({we_expr}),.we2(1\'b0),.out1(ref1),.out2(ref2));')
   else:texts.append(f'single_port_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) reference(.clk(clk),.addr(addr1),.data(effective_data),.we({we_expr}),.out(ref1));assign ref2=ref1;assign phy2=phy1;')
   for lane,(cn,c) in sorted(lanes.items()):
    z=c['connections'];assert (c['type']=='dual_port_ram')==dp
    for p in ['clk',we]+(['addr1','addr2'] if dp else ['addr']):assert z[p]==common[p]
    pins=[]
    for p,bs in z.items():
     value=f'phy{1 if p in ["out","out1"] else 2}[{lane}]' if c['port_directions'][p]=='output' else vec(bs);pins.append('.'+p+'('+value+')')
    texts.append(f'{c["type"]} #(.ADDR_WIDTH(11),.DATA_WIDTH(1)) lane{lane}('+','.join(pins)+');')
   if ro:
    texts.append(f'''initial begin
for(j=0;j<512;j=j+1)begin addr1=j%{1<<a};#5;clk=1;#1;
if(ref1 !== {{{w}{{1'bx}}}} || phy1 !== ref1)$fatal(1,"RO unknown-state mismatch group{index}");#4;clk=0;end
$display("SHALLOW_RO_UNINITIALIZED_ONLY group={index} cycles=512 writes=0");done=1;
end endmodule''')
   else:
    texts.append(f'''initial begin
for(i=0;i<{1<<a};i=i+1)begin
addr1=i;addr2=(i+1)%{1<<a};data=i*37+5;we=1;#5;clk=1;#1;
if(ref1 !== effective_data || phy1 !== ref1)$fatal(1,"public initialization mismatch group{index}");#4;clk=0;
end
for(j=0;j<512;j=j+1)begin
rng=rng*1664525+1013904223;addr1=(rng>>16)%{1<<a};rng=rng*1664525+1013904223;addr2=(rng>>16)%{1<<a};if(addr2==addr1)addr2=addr1^1;
for(i=0;i<{w};i=i+1)begin rng=rng*1664525+1013904223;data[i]=rng[24];end
we=j%3==0;#5;clk=1;#1;
if(ref1 !== phy1 || ref2 !== phy2 || (^ref1 === 1'bx) || (^ref2 === 1'bx))$fatal(1,"defined read mismatch group{index} cycle=%0d",j);
held1=ref1;held2=ref2;#4;clk=0;addr1=addr1^1;addr2=addr2^1;#1;
if(ref1 !== held1 || phy1 !== held1 || ref2 !== held2 || phy2 !== held2)$fatal(1,"hold mismatch group{index}");
end
$display("SHALLOW_WRITABLE_TRACE_PASS group={index} initialized_rows={1<<a} cycles=512");done=1;
end endmodule''')
   receipts.append({'group':index,'source':row['source'],'instance':g['source_instance'],'address_bits':a,'width':w,'read_only':ro,'physical_lanes':{str(k):n for k,(n,_) in lanes.items()},'input_node_renaming':{str(k):v for k,v in node_map.items()},'effective_data_bits_lsb_first':effective});index+=1
 assert index==12;texts.append('module tb;wire[11:0] done;'+''.join(f'checker{i} g{i}(done[{i}]);' for i in range(12))+'initial begin wait(&done);$display("ALL_SHALLOW_GROUPS_COMPLETE");$finish;end endmodule');(D/'fixtures.v').write_text('\n'.join(texts)+'\n');(D/'extraction_manifest.json').write_text(json.dumps({'groups':receipts},indent=2)+'\n');(D/'run.tcl').write_text('run all\nquit\n');rows=[]
 for cmd in [[str(BIN/'xvlog'),str(library),str(D/'fixtures.v')],[str(BIN/'xelab'),'tb','-s','shallow'],[str(BIN/'xsim'),'shallow','-tclbatch',str(D/'run.tcl')]]:
  with (D/(Path(cmd[0]).name+'.stdout.log')).open('w') as out:code=subprocess.call(cmd,cwd=D,stdout=out,stderr=subprocess.STDOUT)
  rows.append({'command':cmd,'exit_code':code});print(Path(cmd[0]).name,code,flush=True)
  if code:break
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
