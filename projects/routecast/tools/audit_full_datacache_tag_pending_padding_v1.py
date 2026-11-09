"""Bind pending-address padding invariant to actual structural register cells."""
import hashlib, json, subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1]
f=R/'experiments/full_ram_mapping_candidate_v1_2026-10-09/structural.json'
m=max(json.loads(f.read_text())['modules'].values(),key=lambda x:len(x.get('cells',{})))
D=R/'experiments/full_datacache_tag_pending_padding_v1_2026-10-09';D.mkdir(exist_ok=True)
rows=[]
for i in range(2):
 prefix=f'dataCache_1.ways_0_tags.s{i}'
 pa=m['netnames'][prefix+'.pa'];pw=m['netnames'][prefix+'.pw'];ram=m['cells'][prefix+'.ram']
 def driver(bits):
  matches=[(name,c) for name,c in m['cells'].items() if c['connections'].get('Q')==bits]
  assert len(matches)==1
  return matches[0]
 an,ac=driver(pa['bits']);wn,wc=driver(pw['bits'])
 assert ac['type']==wc['type']=='$dff'
 assert ac['connections']['CLK']==wc['connections']['CLK']==ram['connections']['clk']==[254]
 assert ac['parameters']['CLK_POLARITY']==wc['parameters']['CLK_POLARITY']=='1'
 assert pw['attributes']['init']=='0' and 'init' not in pa['attributes']
 assert ac['connections']['D'][7:]==['0']*3
 assert ram['connections']['we1']==pw['bits'] and ram['connections']['addr1']==pa['bits']
 rows.append({'slice':prefix,'pa_cell':an,'pw_cell':wn,'pa_connections':ac['connections'],'pw_connections':wc['connections'],'pw_init':'0','pa_init':None,'macro_write_enable':ram['connections']['we1'],'macro_write_address':ram['connections']['addr1']})
# Exact base: pending=0, padding arbitrary. Exact post-edge: padding D=0,
# incoming write arbitrary. Counterexample control deliberately corrupts D padding.
(D/'miter.v').write_text('module miter(input [2:0] initial_padding,input incoming_write,output base_bad,step_bad,negative_bad);\nassign base_bad=1\'b0 & (|initial_padding);\nassign step_bad=incoming_write & (|3\'b000);\nassign negative_bad=incoming_write & (|3\'b001);\nendmodule\n')
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys'
results={}
for target in ['base_bad','step_bad','negative_bad']:
 p=subprocess.run([str(y),'-p',f'read_verilog miter.v; prep -top miter; sat -verify -prove {target} 0 -show-inputs'],cwd=D,capture_output=True,text=True,timeout=30)
 (D/(target+'.log')).write_text(p.stdout+p.stderr)
 results[target]={'exit_code':p.returncode,'success':'SAT proof finished - no model found: SUCCESS!' in p.stdout,'counterexample_rejected':'proof did fail' in p.stderr+p.stdout}
assert all(results[t]['success'] and results[t]['exit_code']==0 for t in ['base_bad','step_bad'])
assert results['negative_bad']['exit_code']!=0 and results['negative_bad']['counterexample_rejected']
out={'rows':rows,'results':results,'invariant':'pending_write=0 OR pending_address[9:7]=0','scope':'Actual structural register binding plus binary-clock base and unconditional one-edge preservation. Address padding initial values remain arbitrary. Does not prove all macro pin correspondence, raw RAM output equality, four-state global events, or Full replay admission.','source_sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'slices':len(rows),'results':results,'scope':out['scope']},indent=2))
