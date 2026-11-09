"""Same pinned functional primitive, free versus actual constant-disabled port."""
import json,os,resource,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'ram_mapping_semantics_v1_2026-10-20/disabled_port_probe'
def load(p):return json.loads(p.read_text())
def main():
 D.mkdir();m=load(E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v4.json');binary=Path(m['yosys_binary']);lib=Path(m['primitive_library']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 protocol=dict(status='FROZEN_BEFORE_DISABLED_PORT_PROBE',cases=['free_we2','constant_zero_we2'],ADDR_WIDTH=1,DATA_WIDTH=2,scope='Tiny original functional primitive with identical hierarchy/flatten/proc/opt/check. Tiedport condition observed structurally in realcandidate RTLIL. No collision assumptions,clock/reset rewrite or fullsize proof.',bindings={str(p):sha(p) for p in [binary,lib,runtime,Path(__file__)]});(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for mode in protocol['cases']:
  folder=D/mode;folder.mkdir();port='we2' if mode=='free_we2' else "1'b0";top=folder/'probe.v';top.write_text('module probe(input clk,input addr1,addr2,input[1:0]data1,data2,input we1,we2,output[1:0]out1,out2); dual_port_ram #(.ADDR_WIDTH(1),.DATA_WIDTH(2)) dut(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.data2(data2),.we1(we1),.we2('+port+'),.out1(out1),.out2(out2)); endmodule\n');commands=folder/'commands.ys';commands.write_text(f'read_verilog "{lib}"\nread_verilog "{top}"\nhierarchy -check -top probe\nflatten\nproc\nopt\nwrite_json "{folder/"proc.json"}"\ncheck -assert\n')
  def limits():resource.setrlimit(resource.RLIMIT_AS,(2<<30,2<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  tick=time.perf_counter()
  with (folder/'yosys.log').open('x') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(commands)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  design=load(folder/'proc.json');types={}
  for module in design['modules'].values():
   for c in module.get('cells',{}).values():types[c['type']]=types.get(c['type'],0)+1
  text=(folder/'yosys.log').read_text();row=dict(mode=mode,exit_code=code,seconds=time.perf_counter()-tick,cell_types=types,multiple_driver_warning='multiple conflicting drivers' in text.lower(),formal_or_native_equivalence=False);rows.append(row);print('DISABLED_RAM_PORT',row,flush=True)
 (D/'results.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
