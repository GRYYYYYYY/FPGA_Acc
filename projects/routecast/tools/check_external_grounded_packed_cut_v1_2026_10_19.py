"""Explicit-ground native loaded LUT cut versus frozen mapped cut, exact FF boundary."""
import json,subprocess,time,resource
from pathlib import Path
from pre_route_endpoints import sha
from verify_external_family_cut_v1_2026_10_18 import lines
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_grounded_packed_cut_v1_2026-10-19';out.mkdir(exist_ok=False);native=R/'experiments/prospective_external_family_native_packed_LUTs_v1_2026-10-19';np=native/'verification.json';proof=read(np);assert all(sha(p)==h for p,h in proof['bindings'].items());statep=R/'experiments/prospective_external_family_packed_FF_v1_2026-10-18/verification.json';state=read(statep);assert state['status']=='all1938_packed_FF_bits_and_public_ports_verified' and state['FF_bits']==1938;assert all(sha(p)==h for p,h in state['bindings'].items());cutroot=R/'experiments/prospective_external_family_compile_cut_v2_2026-10-18';reference=cutroot/'mapped_cut.blif';frozen=read(R/'experiments/prospective_external_family_compile_verification_v1_2026-10-18/verification.json');assert frozen['bindings'][str(reference)]==sha(reference);records=lines(reference)
 def header(key):
  rows=[r[1:] for r in records if r[0]==key];assert len(rows)==1;return rows[0]
 inputs=header('.inputs');outputs=header('.outputs');original=lines(cutroot/'design.blif');ffs=[r for r in original if r[0]=='.latch'];assert len(ffs)==1938;publicin=next(r[1:] for r in original if r[0]=='.inputs');publicout=next(r[1:] for r in original if r[0]=='.outputs');assert inputs==list(dict.fromkeys(publicin+[r[2] for r in ffs]));assert outputs==list(dict.fromkeys(publicout+[r[1] for r in ffs]+['clk']));assert all(r[3:5]==['re','clk'] for r in ffs)
 target=out/'native_grounded_cut.blif';loaded=native/'loaded_LUTs.tsv';drivers=set(inputs);uses=set(outputs);count=0;assignmentrows=0
 with target.open('x') as f:
  f.write('.model cut\n.inputs '+' '.join(inputs)+'\n.outputs '+' '.join(outputs)+'\n')
  for line in loaded.open():
   name,width,signalline,mask=line.rstrip('\n').split('\t');signals=signalline.split(',');assert len(signals)==int(width) and len(mask)==1<<int(width);connected=[i for i,s in enumerate(signals) if s!='open'];names=[signals[i] for i in connected];assert name not in drivers and len(names)==len(set(names));drivers.add(name);uses.update(names);f.write('.names '+' '.join(names+[name])+'\n');n=len(names)
   for value in range(1<<n):
    physical=sum(((value>>j)&1)<<i for j,i in enumerate(connected));assert mask[physical] in '01';assignmentrows+=1
    if mask[physical]=='1':f.write(''.join(str((value>>j)&1) for j in range(n))+' 1\n')
   count+=1
  f.write('.end\n')
 assert count==6483 and not uses-drivers and assignmentrows==184360;abc=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/abc/abc';oldprotocol=read(cutroot/'protocol.json');assert oldprotocol['bindings'][str(abc)]==sha(abc);command=[str(abc),'-c',f'cec "{reference}" "{target}"'];paths=[np,statep,loaded,reference,cutroot/'design.blif',target,abc,Path(__file__).resolve()];bindings={str(p):sha(p) for p in paths};protocol=dict(command=command,bindings=bindings,primary_inputs=len(publicin),primary_outputs=len(publicout),FF_state_pairs=len(ffs),cut_inputs=len(inputs),cut_outputs=len(outputs),LUTs=count,unused_input_contract='Explicit ground for functional cut only; native default unconnected writer is unchanged.',scope='Derived from native loaded masks and native physical input nets. All FF Qs become independent inputs; all FF Ds and public outputs plus clock are outputs. Packed FF/control/IO correctness inherited from exact1938-bit source-bound audit. Boolean combinational CEC only; no full HDL/four-state/timing/unrestricted power-up or strict family claim.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2));start=time.perf_counter()
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 with (out/'cec.log').open('x') as f:result=subprocess.run(command,cwd=out,stdout=f,stderr=subprocess.STDOUT,preexec_fn=limit)
 text=(out/'cec.log').read_text();passed=result.returncode==0 and 'Networks are equivalent' in text and 'NOT EQUIVALENT' not in text
 for p,h in bindings.items():assert sha(p)==h
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='EXPLICIT_GROUND_NATIVE_PACKED_CUT_CEC_PASS' if passed else 'EXPLICIT_GROUND_NATIVE_PACKED_CUT_CEC_NOT_PROVEN',passed=passed,exit_code=result.returncode,component_seconds=time.perf_counter()-start,LUTs=count,FF_state_pairs=1938,cut_inputs=len(inputs),cut_outputs=len(outputs),bindings={str(p):sha(p) for p in [out/'protocol.json',out/'cec.log']},scope=protocol['scope']),f,indent=2)
 print('GROUNDED_NATIVE_PACKED_CEC',passed,result.returncode,'inputs',len(inputs),'outputs',len(outputs));assert passed
if __name__=='__main__':main()
