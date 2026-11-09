"""Explicit simulator library-path diagnosis in a copied output namespace."""
import json,hashlib,shutil,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'briey_pad_wrapper_xsim_v1_2026-10-09';D=E/'briey_xsim_runtime_diagnosis_v2_2026-10-09';D.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=json.loads((B/'receipt.json').read_text())
for p,h in {**receipt['bindings'],**receipt['files']}.items():assert sha(p)==h
shutil.copytree(B/'xsim.dir',D/'xsim.dir');settings=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/settings64.sh');lib=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vivado/2022.2/lib/lnx64.o');prefix='source '+str(settings)+'; export LD_LIBRARY_PATH='+str(lib)+':"${LD_LIBRARY_PATH:-}"; '
commands=['ldd xsim.dir/pad_tb/xsimk','xsim pad_tb -runall'];bindings={str(p):sha(p) for p in (Path(__file__).resolve(),B/'receipt.json',B/'tb.sv',lib/'librdi_simulator_kernel.so')};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,commands=commands,explicit_library=str(lib),timeout_each_s=60),indent=2)+'\n');results=[]
for i,cmd in enumerate(commands):
 with (D/f'stage{i}.log').open('x') as log:
  try:code=subprocess.run(['bash','-c',prefix+cmd],cwd=D,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
  except subprocess.TimeoutExpired:code='TIMEOUT'
 results.append(code)
passed='PASS checks=20480' in (D/'stage1.log').read_text();(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,results=results,passed=passed,files={str(p):sha(p) for p in D.rglob('*') if p.is_file()}),indent=2)+'\n');print(results,'passed',passed)
