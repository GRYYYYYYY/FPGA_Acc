"""Actual native/ABC combinational selector miter with explicit state cuts."""
import hashlib,json,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';F=E/'full_native_ram_gates_v3_2026-10-09/gates.json';B=E/'full_ram_init_export_runtime_v8_2026-10-09/design.blif';A=E/'full_native_wrapper_visible_selectors_v1_2026-10-09/selector_audit.json';D=E/'full_native_blif_wrapper_selectors_v1_2026-10-09';D.mkdir(exist_ok=True)
m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})));a=json.loads(A.read_text());targets=sorted({r['q'] for r in a['rows']});cuts={b for p in m['ports'].values() if p['direction']=='input' for b in p['bits']};drivers={}
for name,c in m['cells'].items():
 for p,bs in c['connections'].items():
  if c['port_directions'][p]!='output':continue
  if c['type'].startswith('$_DFF') or c['type']=='dual_port_ram':cuts.update(bs)
  else:
   for b in bs:drivers[b]=(name,c)
lines=B.read_text().replace('\\\n',' ').splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   row=lines[i].split();i+=1
   if row and not row[0].startswith('#'):rows.append(row)
  tables[t[-1]]=(t[1:-1],rows)
leafs=set();assigns={};source_cells={};abc_tables={}
input_alias={name+('['+str(i)+']' if len(p['bits'])>1 else ''):b for name,p in m['ports'].items() if p['direction']=='input' for i,b in enumerate(p['bits'])}
def boundary(b):leafs.add(b);return 'in'+str(b)
def native(b):
 if isinstance(b,str):assert b in ['0','1'];return "1'b"+b
 if b in cuts:return boundary(b)
 key='n'+str(b)
 if key in assigns:return key
 name,c=drivers[b];co=c['connections'];t=c['type'];source_cells[name]=c
 if t=='$_MUX_':rhs=f"{native(co['S'][0])} ? {native(co['B'][0])} : {native(co['A'][0])}"
 elif t=='$_NOT_':rhs='~'+native(co['A'][0])
 else:
  op={'$_AND_':'&','$_OR_':'|','$_XOR_':'^'}[t];rhs=f"{native(co['A'][0])} {op} {native(co['B'][0])}"
 assigns[key]=rhs;return key
def abc(net):
 if net.startswith('b') and net[1:].isdigit() and int(net[1:]) in cuts:return boundary(int(net[1:]))
 if net in input_alias:return boundary(input_alias[net])
 if net in ['const0','const1']:return "1'b"+net[-1]
 key='a'+str(list(tables).index(net))
 if key in assigns:return key
 ins,rows=tables[net];abc_tables[net]={'inputs':ins,'rows':rows};args=[abc(x) for x in ins];terms=[]
 for row in rows:
  if not ins:assert row==['1'];terms.append("1'b1");continue
  assert len(row)==2 and row[1]=='1' and len(row[0])==len(ins)
  term=[f'~({v})' if p=='0' else f'({v})' for p,v in zip(row[0],args) if p!='-'];terms.append(' & '.join(term) if term else "1'b1")
 assigns[key]=' | '.join('('+t+')' for t in terms) if terms else "1'b0";return key
pairs=[(b,native(b),abc('b'+str(b))) for b in targets]
text='module check_selectors('+','.join('input in'+str(b) for b in sorted(leafs))+',output bad);\n'+'\n'.join('wire '+k+'; assign '+k+' = '+v+';' for k,v in assigns.items())+'\nassign bad = '+' | '.join(f'({n} ^ {a})' for b,n,a in pairs)+';\nendmodule\n';(D/'miter.v').write_text(text)
yosys=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';cmd=[str(yosys),'-p',f'read_verilog {D / "miter.v"}; hierarchy -top check_selectors; proc; opt; check -assert; sat -prove bad 0 -show-inputs -show-outputs'];run=subprocess.run(cmd,capture_output=True,text=True,timeout=60);log=run.stdout+run.stderr;(D/'proof.log').write_text(log);passed=run.returncode==0 and 'SAT proof finished - no model found: SUCCESS!' in log
mutated_key=pairs[0][2]
old='assign '+mutated_key+' = '+assigns[mutated_key]+';'
new='assign '+mutated_key+' = ~('+assigns[mutated_key]+');'
assert text.count(old)==1
(D/'negative.v').write_text(text.replace(old,new,1))
negative=subprocess.run([str(yosys),'-p',f'read_verilog {D / "negative.v"}; hierarchy -top check_selectors; proc; opt; check -assert; sat -prove bad 0 -show-inputs -show-outputs'],capture_output=True,text=True,timeout=60)
negative_log=negative.stdout+negative.stderr;(D/'negative.log').write_text(negative_log)
negative_detected=negative.returncode==0 and 'SAT proof finished - model found: FAIL!' in negative_log
assert negative_detected
out={'negative_detected':negative_detected,'negative_mutation':'Invert the first actual ABC selector output expression','target_lanes':len(targets),'boundary_leaves':len(leafs),'native_cells':source_cells,'abc_tables':abc_tables,'pairs':pairs,'exit_code':run.returncode,'sat_passed':passed,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [F,B,A]},'scope':'Two-state actual native gate/ABC truth-table equivalence at all retained wrapper q outputs under shared arbitrary register Q and macro-output boundaries. No state/init coupling, macro event semantics, four-state LUT agreement, exported Verilog or Full admission.'};(D/'selector_equivalence_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'target_lanes':len(targets),'boundary_leaves':len(leafs),'native_cells':len(source_cells),'abc_tables':len(abc_tables),'exit_code':run.returncode,'sat_passed':passed},indent=2));assert passed
