"""All 145 original-source/intermediate output functions, explicit shared cuts."""
import hashlib,json,re,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_external_output_state_closure_v1_2026-10-09';D=E/'full_source_structural_external_outputs_v1_2026-10-09';D.mkdir(exist_ok=True)
files=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',P/'mapping_candidates.json'];s,m=[max(json.loads(f.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{}))) for f in files[:2]];c=json.loads(files[2].read_text());boundary=[r['source_bit'] for r in c['records']];idx={b:i for i,b in enumerate(boundary)};reverse={};constants={}
for r in c['records']:
 candidates=r['mapped_candidates']
 if len(candidates)==1:
  x=candidates[0]
  if isinstance(x,int):assert x not in reverse;reverse[x]=r['source_bit']
  else:constants[r['source_bit']]=x
assert constants=={3149:'0'},constants
names=[n for n,p in s['ports'].items() if p['direction']=='output'];assert set(names)=={n for n,p in m['ports'].items() if p['direction']=='output'}
positions=[{'port':name,'lane':i,'source_bit':a,'mapped_bit':b} for name in names for i,(a,b) in enumerate(zip(s['ports'][name]['bits'],m['ports'][name]['bits']))];assert len(positions)==145 and all(len(s['ports'][n]['bits'])==len(m['ports'][n]['bits']) for n in names)
mods={};lines=[f'module miter(input [{len(boundary)-1}:0] shared,output bad);'];coverage={}
for label,mod in [('source',s),('mapped',m)]:
 roots=list(dict.fromkeys(r['source_bit' if label=='source' else 'mapped_bit'] for r in positions));ri={b:i for i,b in enumerate(roots)};drivers={b:(n,v) for n,v in mod['cells'].items() for p,bs in v['connections'].items() if v['port_directions'][p]=='output' for b in bs if isinstance(b,int)};cut=set(boundary) if label=='source' else set(reverse);used={};leaves=set();todo=list(roots)
 while todo:
  b=todo.pop()
  if not isinstance(b,int):continue
  if b in cut:leaves.add(b);continue
  assert b in drivers,(label,'undriven',b)
  n,v=drivers[b];assert not re.match(r'^\$(?:[as]?dff|dlatch|mem)',v['type']) and v['type']!='dual_port_ram',(label,'uncut state',b,n)
  if n in used:continue
  used[n]=v;todo.extend(b for p,bs in v['connections'].items() if v['port_directions'][p]=='input' for b in bs)
 ports={'roots':{'direction':'output','bits':roots}};con=[f'.roots({label}_roots)'];lines.append(f'wire [{len(roots)-1}:0] {label}_roots;')
 for b in sorted(leaves):ports['i'+str(b)]={'direction':'input','bits':[b]};src=b if label=='source' else reverse[b];con.append(f'.i{b}(shared[{idx[src]}])')
 mods[label]={'attributes':{},'ports':ports,'cells':used,'netnames':{}};lines.append(label+' u_'+label+'('+','.join(con)+');');vector=[f'{label}_roots[{ri[r["source_bit" if label=="source" else "mapped_bit"]]}]' for r in positions];lines.append(f'wire [144:0] {label}_values={{'+','.join(reversed(vector))+'};');coverage[label]={'cells':len(used),'leaves':len(leaves),'roots':len(roots)}
lines.append('assign bad=|(source_values ^ mapped_values); endmodule');(D/'cuts.json').write_text(json.dumps({'modules':mods}));(D/'miter.v').write_text('\n'.join(lines)+'\n');script=f'read_json {D / "cuts.json"}\nread_verilog {D / "miter.v"}\nhierarchy -check -top miter\nflatten\nopt\ncheck -assert\nsat -set shared[{idx[3149]}] 0 -prove bad 0 -show-inputs -show-outputs\n';(D/'check.ys').write_text(script)
yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';start=time.monotonic()
try:
 with (D/'proof.log').open('w') as f:run=subprocess.run([str(yosys),'-s',str(D/'check.ys')],stdout=f,stderr=subprocess.STDOUT,timeout=60)
 log=(D/'proof.log').read_text();code=run.returncode;status='passed' if code==0 and 'SAT proof finished - no model found: SUCCESS!' in log else 'counterexample' if code==0 and 'SAT proof finished - model found: FAIL!' in log else 'error'
except subprocess.TimeoutExpired:code=None;status='terminal_timeout'
negative_text=(D/'miter.v').read_text()
match=re.search(r'wire \[144:0\] mapped_values=\{([^\n]+)\};',negative_text);assert match
terms=match[1].split(',');assert len(terms)==145;terms[-1]='~('+terms[-1]+')'
negative_text=negative_text[:match.start(1)]+','.join(terms)+negative_text[match.end(1):]
(D/'negative.v').write_text(negative_text)
negative_script=script.replace(str(D/'miter.v'),str(D/'negative.v'))
(D/'negative.ys').write_text(negative_script)
with (D/'negative.log').open('w') as f:negative=subprocess.run([str(yosys),'-s',str(D/'negative.ys')],stdout=f,stderr=subprocess.STDOUT,timeout=20)
negative_detected=negative.returncode==0 and 'SAT proof finished - model found: FAIL!' in (D/'negative.log').read_text();assert negative_detected
out={'negative_control':'Invert exactly the first mapped external output observation','negative_detected':negative_detected,'positions':positions,'external_output_positions':len(positions),'status':status,'exit_code':code,'seconds':time.monotonic()-start,'cuts':coverage,'boundary_bits':len(boundary),'constant_premise':constants,'hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [*files,D/'cuts.json',D/'miter.v']},'scope':'Conditional two-state original-source/intermediate all external output functions, under explicit shared register/RAM-visible cut equality and loader_killReg0. No complete initial/inductive relation, source/native bridge, undefined independent-state interpretation, four-state or Full admission.'};(D/'output_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['external_output_positions','status','exit_code','seconds','cuts','boundary_bits']},indent=2));assert status=='passed'
