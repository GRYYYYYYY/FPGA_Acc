"""External ABC combinational cut mapping, CEC and exact FF restoration."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from reconstruct_vexriscv_sequential_netlist import logical_lines
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 old=R/'experiments/prospective_external_family_compile_preflight_v1_2026-10-18/receipt.json';v=json.loads(old.read_text());assert v['exit_status']==1;assert 'No such command: abc' in old.with_name('frontend.log').read_text()
 out=R/'experiments/prospective_external_family_compile_cut_v2_2026-10-18';out.mkdir(exist_ok=False);protocol=json.loads(old.with_name('protocol.json').read_text());bindings={**v['bindings'],str(old):sha(old),str(Path(__file__)):sha(__file__),str(R/'tools/reconstruct_vexriscv_sequential_netlist.py'):sha(R/'tools/reconstruct_vexriscv_sequential_netlist.py')}
 for p,h in bindings.items():assert sha(p)==h
 source=R/'experiments/prospective_external_family_source_v2_2026-10-18';sv=json.loads((source/'source_verification.json').read_text());tool=Path(sv['yosys_path']);abc=tool.parents[1]/'abc/abc';runtime=R/'experiments/prospective_external_family_runtime_v1_2026-10-18';env=os.environ.copy();lib=runtime/'tcl-root/usr/lib/x86_64-linux-gnu';env['LD_LIBRARY_PATH']=str(lib)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 commands=protocol['commands'];prefix=commands[:commands.index('abc -exe "'+str(abc)+'" -lut 6')];prefix+=['check -assert','write_json "'+str(out/'flat.json')+'"','write_blif "'+str(out/'flat.blif')+'"']
 with (out/'frontend.ys').open('x') as f:f.write('\n'.join(prefix)+'\n')
 with (out/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,frontend_commands=prefix,ABC_commands=['read_blif cut.blif; strash; if -K 6; write_blif mapped_cut.blif','cec cut.blif mapped_cut.blif'],policy='Clock/reset/state records never passed through ABC: cut every synchronous FF, preserve exact original .latch records and restore after CEC. No source changes or native labels.',scope='Boolean cut equivalence and FF-boundary preservation, not full HDL/four-state equivalence, packing or strict-family admission.'),f,indent=2)
 phases=[]
 def run(label,cmd):
  tick=time.perf_counter()
  with (out/(label+'.log')).open('x') as log:code=subprocess.call(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
  phases.append(dict(stage=label,exit_code=code,component_seconds=time.perf_counter()-tick));print('SOURCE CUT PREFLIGHT',label,code,flush=True);assert code==0
 run('frontend',[str(tool),'-Q','-T','-s',str(out/'frontend.ys')]);flat=list(logical_lines(out/'flat.blif'));assert sum(x.startswith('.model ') for x in flat)==1 and not any(x.startswith('.subckt ') for x in flat);inputs=next(x.split()[1:] for x in flat if x.startswith('.inputs '));outputs=next(x.split()[1:] for x in flat if x.startswith('.outputs '));state=[x for x in flat if x.startswith('.latch ')];assert state and all(len(x.split())==6 and x.split()[3]=='re' and x.split()[4]=='clk' for x in state)
 cutinputs=list(dict.fromkeys(inputs+[x.split()[2] for x in state]));cutoutputs=list(dict.fromkeys(outputs+[x.split()[1] for x in state]+['clk']));body=[x for x in flat if not x.startswith(('.model ','.inputs ','.outputs ','.latch ','.end'))]
 with (out/'cut.blif').open('x') as f:f.write('\n'.join(['.model cut','.inputs '+' '.join(cutinputs),'.outputs '+' '.join(cutoutputs),*body,'.end'])+'\n')
 run('map',[str(abc),'-c','read_blif cut.blif; strash; if -K 6; write_blif mapped_cut.blif']);run('cec',[str(abc),'-c','cec cut.blif mapped_cut.blif']);assert 'Networks are equivalent' in (out/'cec.log').read_text();mapped=list(logical_lines(out/'mapped_cut.blif'));body=[x for x in mapped if not x.startswith(('.model ','.inputs ','.outputs ','.end'))];assert not any(x.startswith(('.latch ','.subckt ')) for x in body);names=[x.split() for x in body if x.startswith('.names ')];assert names and max(len(x)-2 for x in names)<=6
 drivers=inputs+[x[-1] for x in names]+[x.split()[2] for x in state];uses=outputs+[n for x in names for n in x[1:-1]]+[n for x in state for n in (x.split()[1],x.split()[4])];assert len(drivers)==len(set(drivers)) and not set(uses)-set(drivers)
 with (out/'design.blif').open('x') as f:f.write('\n'.join(['.model chacha','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs),*body,*state,'.end'])+'\n')
 assert [x for x in logical_lines(out/'design.blif') if x.startswith('.latch ')]==state
 for p,h in bindings.items():assert sha(p)==h
 files={str(p):sha(p) for p in out.iterdir() if p.is_file()}
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='LUT6_cut_mapped_CEC_pass_FF_boundary_exact',bindings=bindings,phases=phases,files=files,LUTs=len(names),FF_bits=len(state),primary_inputs=len(inputs),primary_outputs=len(outputs),cut_CEC_pass=True,state_boundary_exact=True,single_driver_all_uses_driven=True,strict_unseen_admitted=False,new_placement_route_jobs=False,scope='Exact archived lowered Boolean cut equivalence with synchronous state records retained. Still requires independent boundary/output audit and full HDL/source/architecture qualification before benchmark use. No native labels or measured FPGA performance.'),f,indent=2)
 print('SOURCE CUT AND STATE PREFLIGHT PASS',len(names),len(state),flush=True)
if __name__=='__main__':main()
