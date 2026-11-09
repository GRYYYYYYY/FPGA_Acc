"""Binary local tag priority check against four actual native gate cells."""
import json,re,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';nf=E/'full_native_ram_gates_v3_2026-10-09/gates.json';rf=E/'full_source_export_fixed_bus_replay_v19_2026-10-09/reference.v';n=max(json.loads(nf.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})))
used={}
for name,c in n['cells'].items():
 if any(b in [3382,8907,5294] for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs):used[name]=c
assert len(used)==3
ports={'high':{'direction':'input','bits':[2016]},'override':{'direction':'input','bits':[7598]},'done':{'direction':'input','bits':[3300]},'we':{'direction':'output','bits':[3382]}}
mod={'attributes':{},'ports':ports,'cells':used,'netnames':{}}
s=rf.read_text();begin=s.index("    tagsWriteCmd_valid = 1'b0;");end=s.index('\n  end',begin);block=s[begin:end];assert block.count('if(')==3
v='module miter(input high,override,done,output bad);\nwire when_DataCache_l850=!high;wire when_DataCache_l1066=override;wire loader_done=done;reg tagsWriteCmd_valid;\nalways @* begin\n'+block+'\nend\nwire native_we;native_cut u(.high(high),.override(override),.done(done),.we(native_we));\nassign bad=tagsWriteCmd_valid ^ native_we;\nendmodule\n'
D=E/'full_tag_write_binary_priority_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'native_cut.json').write_text(json.dumps({'modules':{'native_cut':mod}},indent=2)+'\n');(D/'miter.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for name,text,success in [('positive',v,True),('inverted_override',v.replace('when_DataCache_l1066=override','when_DataCache_l1066=~override'),False)]:
 (D/(name+'.v')).write_text(text);r=subprocess.run([str(y),'-p',f'read_json native_cut.json; read_verilog {name}.v; prep -top miter; flatten; sat -verify -prove bad 0 -show-inputs'],cwd=D,capture_output=True,text=True,timeout=30);log=r.stdout+r.stderr;(D/(name+'.log')).write_text(log)
 assert (r.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in log) if success else (r.returncode!=0 and 'proof did fail' in log)
 results[name]={'exit_code':r.returncode,'expected_success':success}
out={'results':results,'actual_native_gate_count':3,'source_priority_block':block,'scope':'All binary high/override/done combinations for local source tag command priority vs actual native incomingWE gate cone. Corresponding upstream inputs remain premises. Does not change or admit original four-state frozen replay, prove global initial states, or physical hardware equivalence.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [nf,rf,D/'native_cut.json',D/'positive.log',D/'inverted_override.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'results':results,'scope':out['scope']},indent=2))
