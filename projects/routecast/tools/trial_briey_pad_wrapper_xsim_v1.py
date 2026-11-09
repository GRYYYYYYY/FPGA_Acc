"""Four-state HDL simulation of actual original mux and lowered pad-port bindings."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'briey_pad_wrapper_xsim_v1_2026-10-09';D.mkdir(exist_ok=False);A=E/'briey_bidir_boundary_v1_2026-10-09/design.json';B=E/'briey_bidir_lowering_v1_2026-10-09/design.json';a=json.loads(A.read_text())['modules']['Briey'];b=json.loads(B.read_text())['modules']['Briey'];records=[]
for name,p in a['ports'].items():
 if p['direction']!='inout':continue
 for index,bit in enumerate(p['bits']):
  choices=[(c,i) for c in a['cells'].values() if c['type']=='$mux' for i,x in enumerate(c['connections']['Y']) if x==bit];assert len(choices)==1;c,i=choices[0];assert c['connections']['A'][i]=='z'
  records.append((c['connections']['B'][i],c['connections']['S'][0],b['ports'][name+'__pad_out']['bits'][index],b['ports'][name+'__pad_oe']['bits'][index]))
bits=sorted({x for row in records for x in row if type(x)==int});token=lambda v:'b'+str(v) if type(v)==int else "1'b"+v
lines=['module tb;','function automatic logic val(input integer n); case(n%4) 0:val=0;1:val=1;2:val=1\'bx;3:val=1\'bz;endcase endfunction','integer t; integer checks=0; reg ext_data,ext_oe;']+['reg b'+str(x)+';' for x in bits]
for i,(d,en,ld,le) in enumerate(records):
 lines+= [f'tri orig{i},mapped{i};',f'assign orig{i} = {token(en)} ? {token(d)} : 1\'bz;',f'assign mapped{i} = {token(le)} ? {token(ld)} : 1\'bz;',f'assign orig{i} = ext_oe ? ext_data : 1\'bz;',f'assign mapped{i} = ext_oe ? ext_data : 1\'bz;']
lines+=['initial begin','for(t=0;t<256;t=t+1) begin','ext_data=val(t);ext_oe=val(t/4);']
lines +=[f'b{x}=val(t/{16 if i%2 else 64}+{i%4});' for i,x in enumerate(bits)]
lines+=['#1;']+[f'if(orig{i} !== mapped{i}) $fatal(1,"pad mismatch {i}"); else checks=checks+1;' for i in range(len(records))]+['end','$display("PASS checks=%0d",checks);$finish;end','endmodule'];(D/'tb.sv').write_text('\n'.join(lines)+'\n')
settings=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/settings64.sh');bin=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/bin');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();paths=[A,B,Path(__file__).resolve(),D/'tb.sv',settings]+[bin/x for x in ('xvlog','xelab','xsim')];bindings={str(p):sha(p) for p in paths};commands=['xvlog --sv tb.sv','xelab tb -s pad_tb','xsim pad_tb -runall'];(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,timeout_each_s=120,scope='External wrapper boundary four-state simulation only; no complete Briey internal-circuit equivalence or timing claim.'),indent=2)+'\n')
results=[]
for i,cmd in enumerate(commands):
 with (D/f'stage{i}.log').open('x') as log:
  try:code=subprocess.run(['bash','-c','source '+str(settings)+'; '+cmd],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=120).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 results.append(code)
 if code!=0:break
passed=results==[0,0,0] and 'PASS checks=20480' in (D/'stage2.log').read_text();(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,passed=passed,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()}),indent=2)+'\n');print('results',results,'passed',passed,flush=True)
