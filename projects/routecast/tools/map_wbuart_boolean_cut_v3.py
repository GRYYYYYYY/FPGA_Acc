"""External LUT6 Boolean-cut mapping; exact lowered-state restoration."""
import hashlib,json,os,subprocess,time
from pathlib import Path
from reconstruct_vexriscv_sequential_netlist import logical_lines
R=Path(__file__).resolve().parents[1];I=R/'experiments/wbuart_frontend_v1_2026-10-20';O=R/'experiments/wbuart_boolean_cut_v3_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):
 with (O/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
def main():
 O.mkdir(exist_ok=False);v=json.loads((I/'verification.json').read_text());assert v['exit_status']==0 and sha(I/'mapped.json')==v['bindings']['mapped.json']
 y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';abc=y.parents[1]/'abc/abc';assert abc.is_file()
 lib=R/'experiments/prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu';env=os.environ.copy();env['LD_LIBRARY_PATH']=str(lib)+':'+env.get('LD_LIBRARY_PATH','')
 script='read_json '+str(I/'mapped.json')+'\ndffunmap\ntechmap\nopt_clean\ncheck -assert\nwrite_json '+str(O/'flat.json')+'\nwrite_blif '+str(O/'flat.blif')+'\n';(O/'frontend.ys').write_text(script)
 protocol={'bindings':{str(p):sha(p) for p in [I/'mapped.json',y,abc,Path(__file__),O/'frontend.ys',R/'tools/reconstruct_vexriscv_sequential_netlist.py']},'commands':['dffunmap; techmap; opt_clean; check -assert; write_json; write_blif','read_blif cut.blif; strash; if -K 6; write_blif mapped_cut.blif','cec cut.blif mapped_cut.blif'],'timeout_per_phase_seconds':120,'policy':'Freeze default LUT6 mapping; cut every lowered synchronous state bit, restore exact latch records. No source edits, parameter tuning, undef/default-X rewrite or labels. Boolean cut CEC is not original HDL or four-state proof.'};save('protocol.json',protocol);phases=[]
 def run(label,cmd):
  t=time.perf_counter()
  with (O/(label+'.log')).open('x') as f:p=subprocess.run(cmd,cwd=O,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=120)
  phases.append({'stage':label,'exit_status':p.returncode,'seconds':time.perf_counter()-t});assert p.returncode==0
 run('frontend',[str(y),'-Q','-T','-s',str(O/'frontend.ys')]);flat=list(logical_lines(O/'flat.blif'));assert not any(x.startswith('.subckt ') for x in flat)
 inputs=next(x.split()[1:] for x in flat if x.startswith('.inputs '));outputs=next(x.split()[1:] for x in flat if x.startswith('.outputs '));state=[x for x in flat if x.startswith('.latch ')];assert len(state)==598 and all(len(x.split())==6 and x.split()[3]=='re' for x in state)
 ci=list(dict.fromkeys(inputs+[x.split()[2] for x in state]));co=list(dict.fromkeys(outputs+[x.split()[1] for x in state]+[x.split()[4] for x in state]));body=[x for x in flat if not x.startswith(('.model ','.inputs ','.outputs ','.latch ','.end'))]
 # Keep precisely the output/next-state/clock cone; never ground dangling names.
 nodes={}; current=None
 for line in body:
  if not line.strip() or line.lstrip().startswith('#'):continue
  if line.startswith('.names '):
   tokens=line.split();current=tokens[-1];assert current not in nodes;nodes[current]=[tokens[1:-1],[line]]
  elif line.startswith('.'):
   raise AssertionError('Unsupported BLIF directive '+line)
  elif line.strip():
   assert current is not None;nodes[current][1].append(line)
 relevant=set();todo=list(co);undriven=set()
 while todo:
  n=todo.pop()
  if n in relevant or n in ci:continue
  relevant.add(n)
  if n not in nodes:undriven.add(n);continue
  todo.extend(nodes[n][0])
 assert not undriven,sorted(undriven)
 omitted=sorted(set(nodes)-relevant)
 body=[line for n,(_,lines) in nodes.items() if n in relevant for line in lines]
 save('output_cone_audit.json',{'retained_nodes':len(relevant),'omitted_output_unreachable_nodes':omitted,'reachable_undriven':sorted(undriven),'policy':'Remove only nodes outside every output, next-state D and clock cone. No default constants assigned.'})
 (O/'cut.blif').write_text('\n'.join(['.model cut','.inputs '+' '.join(ci),'.outputs '+' '.join(co),*body,'.end'])+'\n')
 run('map',[str(abc),'-c',protocol['commands'][1]]);run('cec',[str(abc),'-c',protocol['commands'][2]]);assert 'Networks are equivalent' in (O/'cec.log').read_text();assert 'non-driven' not in (O/'cec.log').read_text() and 'non-driven' not in (O/'map.log').read_text()
 mapped=list(logical_lines(O/'mapped_cut.blif'));body=[x for x in mapped if not x.startswith(('.model ','.inputs ','.outputs ','.end'))];assert not any(x.startswith(('.latch ','.subckt ')) for x in body);names=[x.split() for x in body if x.startswith('.names ')];assert names and max(len(x)-2 for x in names)<=6
 drivers=inputs+[x[-1] for x in names]+[x.split()[2] for x in state];uses=outputs+[n for x in names for n in x[1:-1]]+[n for x in state for n in (x.split()[1],x.split()[4])];assert len(drivers)==len(set(drivers)) and not set(uses)-set(drivers)
 (O/'design.blif').write_text('\n'.join(['.model wbuart','.inputs '+' '.join(inputs),'.outputs '+' '.join(outputs),*body,*state,'.end'])+'\n');assert [x for x in logical_lines(O/'design.blif') if x.startswith('.latch ')]==state
 for p,h in protocol['bindings'].items():assert sha(Path(p))==h
 save('verification.json',{'status':'BOOLEAN_CUT_CEC_PASS_EXACT_LOWERED_STATE_RESTORATION','phases':phases,'FF_bits':len(state),'LUTs':len(names),'primary_inputs':len(inputs),'primary_outputs':len(outputs),'all_uses_driven_single_driver':True,'strict_unseen_certified':False,'original_HDL_equivalence_proven':False,'physical_input_admitted':False,'new_route_labels':False,'bindings':{p.name:sha(p) for p in O.iterdir() if p.is_file()}});print('CUT_CEC_PASS',len(state),len(names),flush=True)
if __name__=='__main__':main()
