"""Actual VTR mapper on frozen source RAM shapes; no new layout/route labels."""
import json,os,resource,subprocess,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'standard_parmys_ram_mapping_v2_2026-10-21'
def load(p):return json.loads(p.read_text())
def main():
 D.mkdir(exist_ok=False);m=load(E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json');binary=Path(m['yosys_binary']);library=Path(m['primitive_library']);runtime=Path(m['runtime_library']);plugin=binary.parents[1]/'share/yosys/plugins/parmys.so';arch=E/'async_reset_arch_candidate_v2_2026-10-08/architecture.xml';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 cases=[dict(name='sp10x32',model='single_port_ram',address=10,width=32),dict(name='dp4x32',model='dual_port_ram',address=4,width=32),dict(name='dp13x32',model='dual_port_ram',address=13,width=32),dict(name='dp16x36',model='dual_port_ram',address=16,width=36)];protocol=dict(status='FROZEN_BEFORE_ORIGINAL_PAR MYS_MAPPING'.replace('PAR MYS','PARMYS'),cases=cases,scope='Shapes drawn from actualMCML/mkDelayRAMinterfaces. Originalplugin/architecture/functionalprimitivebytes;no custombankRTL,sourceclock/resetrewrite or nativepack/place/route. Mapping success not functional-equivalence proof.',AS_limit_GiB=8,bindings={str(p):sha(p) for p in [Path(__file__),binary,library,runtime,plugin,arch]});(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for c in cases:
  folder=D/c['name'];folder.mkdir();a,w=c['address'],c['width'];top=folder/'probe.v'
  if c['model']=='single_port_ram':text=f'module probe(input clk,input[{a-1}:0] addr,input[{w-1}:0] data,input we,output[{w-1}:0] out); single_port_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) dut(.clk(clk),.addr(addr),.data(data),.we(we),.out(out)); endmodule\n'
  else:text=f'module probe(input clk,input[{a-1}:0] addr1,addr2,input[{w-1}:0] data1,input we1,output[{w-1}:0] out1,out2); dual_port_ram #(.ADDR_WIDTH({a}),.DATA_WIDTH({w})) dut(.clk(clk),.addr1(addr1),.addr2(addr2),.data1(data1),.data2({w}\'b0),.we1(we1),.we2(1\'b0),.out1(out1),.out2(out2)); endmodule\n'
  top.write_text(text);commands=folder/'commands.ys';commands.write_text(f'plugin -i "{plugin}"\nread_verilog -nomem2reg "{library}"\nparmys_arch -a {arch}\nread_verilog "{top}"\nhierarchy -check -top probe\nproc\nopt\nmemory -nomap\nflatten\nopt\nparmys -a {arch} -nopass\nopt\ncheck -assert\nwrite_json "{folder/"mapped.json"}"\nwrite_blif -true + vcc -false + gnd -undef + unconn -blackbox "{folder/"mapped.blif"}"\n')
  def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  tick=time.perf_counter()
  with (folder/'yosys.log').open('x') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(commands)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  row=dict(case=c,exit_code=code,seconds=time.perf_counter()-tick,functional_equivalence_proven=False,native_architecture_admitted=False)
  if code==0:
   design=load(folder/'mapped.json');types=Counter(x['type'] for mod in design['modules'].values() for x in mod.get('cells',{}).values());row['cell_types']=dict(types)
  rows.append(row);(D/'progress.json').write_text(json.dumps(rows,indent=2)+'\n');print('STANDARD_RAM_MAPPING',c['name'],code,row['seconds'],flush=True)
 (D/'results.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
