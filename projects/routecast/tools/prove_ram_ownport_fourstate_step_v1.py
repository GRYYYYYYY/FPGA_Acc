"""Explicit four-valued stable-event RAM recurrence, conditional state correspondence."""
import json,hashlib,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_ownport_fourstate_step_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);config=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(config['yosys_binary']);runtime=Path(config['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Per-lane explicit4value encoding00=0,01=1,10=X,11=Z. Address knownness/value bitplanes collapse X/Z only for address lookup validity. Known1 enable plus fully-known address writes; unknown-address write ignored; unknown-address read X. Compare logical rows to physical2048rows embedded at prefix0, arbitrary matching initial contents. Stable-event/post-settle sampling only, not HDL delta-cycle scheduling or whole-source equivalence. Exact primitive behavior separately checked with original HDL.','address_widths':[2,3,4],'bindings':{str(p):sha(p) for p in [Path(__file__),binary,runtime]}},indent=2)+'\n');rows=[]
 for a in [2,3,4]:
  n=1<<a
  for mode in ['relation_step','truncated_address_negative','old_read_negative','zero_content_negative']:
   f=D/f'a{a}_{mode}';f.mkdir();pa="{{"+str(11-a)+"{1'b0}},address}" if mode!='truncated_address_negative' else "{{"+str(12-a)+"{1'b0}},address["+str(a-2)+":0]}"
   read='physical_next[2*physical_address +:2]' if mode!='old_read_negative' else 'physical_memory[2*physical_address +:2]'
   if mode=='zero_content_negative':read="2'b00"
   verilog=f'''module proof(input[{a-1}:0]address,known,input[1:0]enable,data,input[{2*n-1}:0]logical_memory,input[4095:0]physical_memory,output ok);
wire address_defined=&known;wire[10:0]physical_address={pa};
reg[{2*n-1}:0]logical_next;reg[4095:0]physical_next;
always @* begin
logical_next=logical_memory;physical_next=physical_memory;
if(enable==2'b01 && address_defined)begin logical_next[2*address +:2]=data;physical_next[2*physical_address +:2]=data;end
end
wire[1:0]logical_out=address_defined?logical_next[2*address +:2]:2'b10;
wire[1:0]physical_out=address_defined?{read}:2'b10;
wire pre=(logical_memory==physical_memory[{2*n-1}:0]);
assign ok= !pre || ((logical_next==physical_next[{2*n-1}:0]) && logical_out==physical_out && physical_next[4095:{2*n}]==physical_memory[4095:{2*n}]);
endmodule
''';v=f/'proof.v';v.write_text(verilog);ys=f/'commands.ys';ys.write_text(f'read_verilog {v}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat -verify -prove ok 1 -show address,known,enable,data,logical_out,physical_out\n')
   with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT)
   text=(f/'yosys.log').read_text();rows.append({'address_bits':a,'mode':mode,'exit_code':code,'proof_passed':'no model found: SUCCESS' in text,'proof_failed':'proof did fail' in text});(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print(a,mode,code,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
