"""Pointwise array-write relation plus frame property; no large-vector expansion."""
import json,hashlib,subprocess,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_fourstate_projection_v2_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);config=json.loads((E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json').read_text());binary=Path(config['yosys_binary']);runtime=Path(config['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(':'+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');(D/'protocol.json').write_text(json.dumps({'scope':'Arbitrary tracked logical row and arbitrary outside physical row. Four-valued memory/enable/data codes; binary row index plus address knownness. Pointwise array update relation, post-event own-port read and outside-row frame. Initial matching row/read values required, never zero content. Synchronous stable-event contract only, no same-clock HDL scheduling/source-wide equivalence.','bindings':{str(p):sha(p) for p in [Path(__file__),binary,runtime]}},indent=2)+'\n');rows=[]
 for a in [2,3,4]:
  for mode in ['state_read_frame','truncated_address_negative','old_read_negative','zero_content_negative']:
   f=D/f'a{a}_{mode}';f.mkdir();physical="{{"+str(11-a)+"{1'b0}},address}" if mode!='truncated_address_negative' else "{{"+str(12-a)+"{1'b0}},address["+str(a-2)+":0]}";pout='((enable==1)?data:physical_read)' if mode!='old_read_negative' else 'physical_read'
   if mode=='zero_content_negative':pout="2'b00"
   text=f'''module proof(input[{a-1}:0]address,known,row,input[10:0]outside_row,input[1:0]enable,data,logical_cell,physical_cell,logical_read,physical_read,outside_cell,output ok);
wire defined_address=&known;wire write_event=(enable==2'b01)&&defined_address;
wire[10:0]physical_address={physical};wire[10:0]mapped_row={{{{{11-a}{{1'b0}}}},row}};
wire[1:0]logical_next=(write_event && address==row)?data:logical_cell;
wire[1:0]physical_next=(write_event && physical_address==mapped_row)?data:physical_cell;
wire[1:0]outside_next=(write_event && physical_address==outside_row)?data:outside_cell;
wire[1:0]logical_out=defined_address?((enable==1)?data:logical_read):2'b10;
wire[1:0]physical_out=defined_address?{pout}:2'b10;
wire pre=(logical_cell==physical_cell)&&(logical_read==physical_read);
assign ok=(!pre || (logical_next==physical_next && logical_out==physical_out)) && ((outside_row[10:{a}]==0)||outside_next==outside_cell);
endmodule
''';vf=f/'proof.v';vf.write_text(text);ys=f/'commands.ys';ys.write_text(f'read_verilog {vf}\nhierarchy -top proof\nproc\nopt\ncheck -assert\nsat -prove ok 1 -show address,known,row,enable,data,logical_out,physical_out -verify\n')
   with (f/'yosys.log').open('w') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(ys)],cwd=f,env=env,stdout=log,stderr=subprocess.STDOUT)
   log=(f/'yosys.log').read_text();rows.append({'address_bits':a,'mode':mode,'exit_code':code,'proof_passed':'no model found: SUCCESS' in log,'proof_failed':'proof did fail' in log});print(a,mode,code,flush=True)
 (D/'results.json').write_text(json.dumps({'rows':rows},indent=2)+'\n')
if __name__=='__main__':main()
