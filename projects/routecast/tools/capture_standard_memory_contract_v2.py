"""Capture actual pinned RTLIL memory semantics without mapping to gates/RAMs."""
import json,os,resource,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'preroute_family_admission_v1_2026-10-20';D=E/'ram_mapping_semantics_v1_2026-10-20/standard_memory_contract_v2'
def load(p):return json.loads(p.read_text())
def number(v):return int(v,2) if isinstance(v,str) else int(v)
def main():
 D.mkdir();m=load(S/'structure_preflight_manifest_v5.json');binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);assert sha(binary)==m['yosys_sha256'] and sha(runtime)==m['runtime_library_sha256'];env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 protocol=dict(status='FROZEN_ACTUAL_RTLIL_MEMORY_CONTRACT_CAPTURE',stages=['read_json alreadycheckedfunctionalnomem2reg input','memory_dff','memory_collect','opt_clean','check -assert','write_json'],scope='No techmap,memory_map,resetconversion,sourcechange,packing orrouting. Raw memory masks captured,not imposed or interpreted as hardwareproof.',bindings={str(p):sha(p) for p in [S/'structure_preflight_manifest_v5.json',binary,runtime,Path(__file__)]});(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for name in ['mcml','arm_core','mkDelayWorker32B']:
  source=S/'structure_preflight_v5'/name/'proc.json';folder=D/name;folder.mkdir();cmd=folder/'commands.ys';target=folder/'collected.json';cmd.write_text(f'read_json "{source}"\nmemory_dff\nmemory_collect\nopt_clean\ncheck -assert\nwrite_json "{target}"\n')
  def limits():resource.setrlimit(resource.RLIMIT_AS,(8<<30,8<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  tick=time.perf_counter()
  with (folder/'yosys.log').open('x') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(cmd)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  row=dict(name=name,exit_code=code,seconds=time.perf_counter()-tick,input_sha256=sha(source),native_mapping_admitted=False)
  if code==0:
   design=load(target);memories=[]
   for module,obj in design['modules'].items():
    for cellname,cell in obj.get('cells',{}).items():
     if cell['type'] not in ['$mem_v2','$mem']:continue
     p=cell['parameters'];keep=['ABITS','WIDTH','SIZE','RD_PORTS','WR_PORTS','RD_CLK_ENABLE','RD_CLK_POLARITY','RD_TRANSPARENCY_MASK','RD_COLLISION_X_MASK','WR_CLK_ENABLE','WR_CLK_POLARITY','WR_PRIORITY_MASK','RD_SRST_VALUE','RD_ARST_VALUE','RD_INIT_VALUE'];memories.append(dict(module=module,cell=cellname,type=cell['type'],parameters={k:p[k] for k in keep if k in p},width=number(p['WIDTH']),size=number(p['SIZE']),read_ports=number(p['RD_PORTS']),write_ports=number(p['WR_PORTS']),initial_value_all_x=set(p.get('INIT','x'))=={'x'}))
   row.update(status='MEMORY_CONTRACT_CAPTURED',memory_definitions=memories,collected_sha256=sha(target))
  rows.append(row);print('MEMORY_CONTRACT',name,code,len(row.get('memory_definitions',[])),flush=True)
 (D/'results.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
