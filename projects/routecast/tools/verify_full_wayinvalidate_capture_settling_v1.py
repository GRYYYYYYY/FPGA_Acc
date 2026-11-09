"""Original two-stage constant capture settles; initial state remains arbitrary."""
import json,re,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';f=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';s=f.read_text()
blocks=[]
for control,q,d in [('when_DataCache_l771_2','stageA_wayInvalidate','stage0_wayInvalidate'),('when_DataCache_l820','stageB_wayInvalidate','stageA_wayInvalidate')]:
 pattern=r'if\('+control+r'\) begin\s*'+q+r' <= '+d+r';[^\n]*\n\s*end';match=re.search(pattern,s);assert match;blocks.append(match[0])
assert "assign stage0_wayInvalidate = 1'b0;" in s
D=E/'full_wayinvalidate_capture_settling_v1_2026-10-09';D.mkdir(exist_ok=True)
v="module settling(input clk,when_DataCache_l771_2,when_DataCache_l820,output reg stageA_wayInvalidate,stageB_wayInvalidate);\nwire stage0_wayInvalidate=1'b0;\nalways @(posedge clk) begin\n"+'\n'.join(blocks)+'\nend\nendmodule\n';(D/'settling.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for name,steps,skip,expected in [('two_captures',3,2,True),('one_capture_not_enough',2,1,False)]:
 cmd=f'read_verilog settling.v; prep -top settling; flatten; sat -seq {steps} -set when_DataCache_l771_2 1 -set when_DataCache_l820 1 -prove stageB_wayInvalidate 0 -prove-skip {skip} -show-inputs -show-outputs'
 r=subprocess.run([str(y),'-p',cmd],cwd=D,capture_output=True,text=True,timeout=30);log=r.stdout+r.stderr;(D/(name+'.log')).write_text(log)
 marker='SAT proof finished - no model found: SUCCESS!' if expected else 'SAT proof finished - model found: FAIL!';assert r.returncode==0 and marker in log;results[name]={'exit_code':r.returncode,'marker':marker}
out={'results':results,'original_capture_blocks':blocks,'initial_state':'Arbitrary independent A/B, no -set-init-zero, -set-init-def or reset constraints.','premise':'Both actual capture enables asserted for two consecutive edges; arbitrary stall timing not covered.','conclusion':'StageB constant0 relation becomes valid after two enabled pipeline captures, not necessarily at initialization or after one capture.','scope':'Original RTL local capture-chain binary settling lemma. Does not prove actual stageA enable asserted, full four-state/global initialization equivalence or dead/constant state admission. Prior observed source B=X first2 rows remains preserved.','source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['results','initial_state','premise','scope']},indent=2))
