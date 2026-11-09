"""Actual pinned frontend on tiny original VTR primitives; not a large-RAM proof."""
import json,os,resource,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_mapping_semantics_v1_2026-10-20/standard_nomem2reg_tiny'
def load(p):return json.loads(p.read_text())
def main():
 D.mkdir(exist_ok=False);m=load(E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v4.json');binary=Path(m['yosys_binary']);lib=Path(m['primitive_library']);runtime=Path(m['runtime_library']);assert sha(binary)==m['yosys_sha256'] and sha(lib)==m['primitive_library_sha256'] and sha(runtime)==m['runtime_library_sha256'];env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 protocol=dict(status='FROZEN_BEFORE_TINY_FUNCTIONAL_PRIMITIVE_PROBE',cases=['single_port_ram','dual_port_ram'],ADDR_WIDTH=1,DATA_WIDTH=2,stages='Original functional library read as RTL withstandardVTR -nomem2reg,hierarchy,proc,check,write_json,check-assert. No blackbox,async2sync,collisionassumption or source edit.',scope='Diagnose actual compiler representation and driver checks at minimal legal width only;does not prove fullsize/sourcebehavior/targethardware.',bindings={str(p):sha(p) for p in [binary,lib,runtime,Path(__file__)]});(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for model in protocol['cases']:
  folder=D/model;folder.mkdir();top=folder/'probe.v'
  if model=='single_port_ram':text='module probe(input clk,input addr,input[1:0]data,input we,output[1:0]out); single_port_ram #(.ADDR_WIDTH(1),.DATA_WIDTH(2)) dut(.clk(clk),.addr(addr),.data(data),.we(we),.out(out)); endmodule\n'
  else:text='module probe(input clk,input addr1,addr2,input[1:0]data1,data2,input we1,we2,output[1:0]out1,out2); dual_port_ram #(.ADDR_WIDTH(1),.DATA_WIDTH(2)) dut(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.data2(data2),.we1(we1),.we2(we2),.out1(out1),.out2(out2)); endmodule\n'
  top.write_text(text);commands=folder/'commands.ys';commands.write_text(f'read_verilog -nomem2reg "{lib}"\nread_verilog "{top}"\nhierarchy -check -top probe\nproc\ncheck\nwrite_json "{folder/"proc.json"}"\ncheck -assert\n')
  def limits():resource.setrlimit(resource.RLIMIT_AS,(2<<30,2<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  start=time.perf_counter()
  with (folder/'yosys.log').open('x') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(commands)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  text=(folder/'yosys.log').read_text();row=dict(model=model,exit_code=code,seconds=time.perf_counter()-start,multiple_driver_warning='multiple conflicting drivers' in text.lower(),unknown_driver_warning='has no driver' in text.lower(),native_or_large_equivalence_admitted=False);rows.append(row);print('FUNCTIONAL_PRIMITIVE_PROBE',row,flush=True)
 (D/'probe_results.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
