"""Build local CLI using read-only VPR's existing SDC parser library; test frozen development constraints."""
import json,hashlib,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'vexriscv_full_sdc_parser_v1_2026-10-09';D.mkdir(exist_ok=False);root=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';src=root/'libs/EXTERNAL/libsdcparse/src';library=root/'build_tileplace_vpr/libs/EXTERNAL/libsdcparse/libsdcparse.a';S=E/'vexriscv_full_development_sdc_v1_2026-10-09';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prior=json.loads((S/'protocol.json').read_text())
for p,h in prior['bindings'].items():assert sha(p)==h
exe=D/'sdcparse_test';compile=['g++','-std=c++14','-I'+str(src),str(src/'main.cpp'),str(library),'-o',str(exe)];bindings={str(p):sha(p) for p in (Path(__file__).resolve(),src/'main.cpp',src/'sdcparse.hpp',library,S/'protocol.json',S/'development.sdc')};(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,compile=compile,scope='Grammar/parser callback test only, no native clock binding/STA or product timing claim.'),indent=2)+'\n');results=[]
with (D/'compile.log').open('x') as log:code=subprocess.run(compile,stdout=log,stderr=subprocess.STDOUT,timeout=60).returncode
assert code==0;bindings[str(exe)]=sha(exe)
with (D/'parse.log').open('x') as log:code=subprocess.run([str(exe),str(S/'development.sdc')],stdout=log,stderr=subprocess.STDOUT,timeout=15).returncode
assert code==0;text=(D/'parse.log').read_text();assert 'create_clock -period 20.000000' in text and text.count('set_input_delay')==2 and text.count('set_output_delay')==2
bad=D/'invalid.sdc';bad.write_text('create_clock -period invalid {clk}\n')
with (D/'invalid.log').open('x') as log:badcode=subprocess.run([str(exe),str(bad)],stdout=log,stderr=subprocess.STDOUT,timeout=15).returncode
assert badcode!=0
(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,compile_exit_code=0,parse_exit_code=code,invalid_exit_code=badcode,files={str(p):sha(p) for p in D.iterdir() if p.is_file()},scope='Actual VPR-linked SDC grammar parser passed and invalid period rejected. Does not bind post-sweep atom pins or prove timing coverage/STA.'),indent=2)+'\n');print('PASS parser callbacks and invalid period rejection')
