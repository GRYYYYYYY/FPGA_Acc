"""Bounded reset-release equality and definedness of every compared bit."""
import hashlib,json,os,resource,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 base=R/'experiments/prospective_external_family_reset_base_v1_2026-10-18';src=base/'miter.json';adapter=base/'receipt_binding_admission_v1.json';a=json.loads(adapter.read_text())
 for p,h in a['bindings'].items():assert sha(Path(p))==h
 document=json.loads(src.read_text());m=document['modules']['base_miter'];drivers={b:c for c in m['cells'].values() for p,v in c['connections'].items() if c['port_directions'][p]=='output' for b in v};changed=0
 for c in m['cells'].values():
  if c['type']!='$assert':continue
  assert c['connections']['EN']==['1'];join=drivers[c['connections']['A'][0]];assert join['type']=='$logic_or'
  eq=drivers[join['connections']['B'][0]];assert eq['type']=='$eqx';c['connections']['A']=eq['connections']['Y'];changed+=1
 assert changed==1970
 nextbit=1+max(bit for cell in m['cells'].values() for values in cell['connections'].values() for bit in values if isinstance(bit,int))
 extra={}
 for i,c in enumerate(list(m['cells'].values())):
  if c['type']!='$assert':continue
  equal=drivers[c['connections']['A'][0]];assert equal['type']=='$eqx'
  checks=[]
  for j,port in enumerate(['A','B']):
   unknown=nextbit;defined=nextbit+1;nextbit+=2
   extra[f'defined_probe_{i}_{j}']=dict(type='$eqx',parameters=dict(A_WIDTH='1',B_WIDTH='1',Y_WIDTH='1',A_SIGNED='0',B_SIGNED='0'),attributes={},port_directions=dict(A='input',B='input',Y='output'),connections=dict(A=equal['connections'][port],B=['x'],Y=[unknown]))
   extra[f'defined_not_{i}_{j}']=dict(type='$logic_not',parameters=dict(A_WIDTH='1',Y_WIDTH='1',A_SIGNED='0'),attributes={},port_directions=dict(A='input',Y='output'),connections=dict(A=[unknown],Y=[defined]))
   checks.append(defined)
  both=nextbit;final=nextbit+1;nextbit+=2
  for suffix,a,b,y in [('both',checks[0],checks[1],both),('equal',both,c['connections']['A'][0],final)]:
   extra[f'defined_and_{i}_{suffix}']=dict(type='$logic_and',parameters=dict(A_WIDTH='1',B_WIDTH='1',Y_WIDTH='1',A_SIGNED='0',B_SIGNED='0'),attributes={},port_directions=dict(A='input',B='input',Y='output'),connections=dict(A=[a],B=[b],Y=[y]))
  c['connections']['A']=[final]
 m['cells'].update(extra)
 out=R/'experiments/prospective_external_family_reset_defined_v1_2026-10-18';out.mkdir(exist_ok=False);mp=out/'strict_miter.json';mp.write_text(json.dumps(document))
 commands=['read_json "'+str(mp)+'"','hierarchy -top base_miter','opt_clean','sat -seq 3 -enable_undef -set-def-inputs -set-init-def -set-at 1 reset_n 0 -set-at 2 reset_n 0 -set-at 3 reset_n 1 -prove-asserts -prove-skip 1 -verify']
 ys=out/'prove.ys';ys.write_text('\n'.join(commands)+'\n');sv=R/'experiments/prospective_external_family_source_v2_2026-10-18/source_verification.json';v=json.loads(sv.read_text());tool=Path(v['yosys_path']);bindings={str(p):sha(p) for p in [Path(__file__),src,adapter,mp,ys,sv,tool]}
 protocol=dict(bindings=bindings,assertions=changed,commands=commands,scope='Bounded equality AND definedness of both operands at all1970points on frames2and3, reset low frames1and2 and released frame3, arbitrary defined initial state and defined inputs. X/X cannot pass because both operands must be defined; no claim of arbitrary-power-up equivalence, physical reset/clock timing or full HDL equivalence. No target route labels.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2));env=os.environ.copy();lib=R/'experiments/prospective_external_family_runtime_v1_2026-10-18/tcl-root/usr/lib/x86_64-linux-gnu';env['LD_LIBRARY_PATH']=str(lib)+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
 def limits():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 start=time.perf_counter()
 with (out/'prove.log').open('x') as log:
  child=subprocess.Popen([str(tool),'-Q','-T','-s',str(ys)],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,preexec_fn=limits)
  (out/'live_process.json').write_text(json.dumps(dict(pid=child.pid)));print('RESET RELEASE CHILD',child.pid,flush=True);code=child.wait()
 text=(out/'prove.log').read_text();passed=code==0 and 'SAT proof finished - no model found: SUCCESS!' in text
 for p,h in bindings.items():assert sha(Path(p))==h
 files={str(p):sha(p) for p in out.iterdir() if p.is_file()}
 receipt=dict(status='bounded_reset_release_defined_equality_pass' if passed else 'bounded_reset_release_defined_equality_not_proven',bindings=bindings,files=files,exit_code=code,passed=passed,assertions=1970,component_seconds=time.perf_counter()-start,scope=protocol['scope'])
 with (out/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
 print('RESET RELEASE TERMINAL',code,passed,flush=True)
if __name__=='__main__':main()
