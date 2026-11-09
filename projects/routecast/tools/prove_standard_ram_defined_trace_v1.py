"""Paired pinned SAT trace: same RTL, old register expansion vs standard memory IR."""
import json,os,resource,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';ROOT=E/'ram_mapping_semantics_v1_2026-10-20';D=ROOT/'defined_trace_sat'
def load(p):return json.loads(p.read_text())
def main():
 D.mkdir();m=load(E/'preroute_family_admission_v1_2026-10-20/structure_preflight_manifest_v5.json');binary=Path(m['yosys_binary']);runtime=Path(m['runtime_library']);env=os.environ.copy();env['LD_LIBRARY_PATH']=str(runtime.parent)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '');old=ROOT/'disabled_port_probe_v2/constant_zero_we2';new=ROOT/'standard_nomem2reg_disabled_port/constant_zero_we2';assert (old/'probe.v').read_bytes()==(new/'probe.v').read_bytes();protocol=dict(status='FROZEN_PAIRED_DEFINED_TRACE_SAT',time='3RTLILstates represent initial state plus2updates;nozero initialization set.',trace='Step1writeaddress0,data2,readport2address1;step2nowritesandreadaddress0;proveout2=2atstate3.',scope='Defined-input bounded sequential Yosysmodel proof only;not fullHDLfourstate/source-equivalence/alltraces/fullsize/hardware.',bindings={str(p):sha(p) for p in [old/'proc.json',new/'proc.json',old/'probe.v',new/'probe.v',binary,runtime,Path(__file__)]});(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for mode,source in [('old_expansion',old/'proc.json'),('standard_nomem2reg',new/'proc.json')]:
  folder=D/mode;folder.mkdir();commands=folder/'commands.ys';commands.write_text(f'read_json "{source}"\nhierarchy -top probe\nmemory -nomap\nmemory_map\nopt_clean\ncheck -assert\nsat -seq 3 -enable_undef -set-def-inputs -set we2 0 -set we1 0 -set addr1 0 -set addr2 0 -set data1 2 -set data2 0 -set-at 1 we1 1 -set-at 1 addr2 1 -prove out2 2 -prove-skip 2 -show out1,out2 -verify\n')
  def limits():resource.setrlimit(resource.RLIMIT_AS,(2<<30,2<<30));resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  tick=time.perf_counter()
  with (folder/'yosys.log').open('x') as log:code=subprocess.call([str(binary),'-Q','-T','-s',str(commands)],cwd=folder,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  text=(folder/'yosys.log').read_text();row=dict(mode=mode,exit_code=code,seconds=time.perf_counter()-tick,SAT_proof_success='SAT proof finished - no model found: SUCCESS!' in text,proof_failed='proof did fail' in text);rows.append(row);print('RAM_DEFINED_TRACE_SAT',row,flush=True)
 (D/'results.json').write_text(json.dumps(dict(rows=rows),indent=2)+'\n')
if __name__=='__main__':main()
