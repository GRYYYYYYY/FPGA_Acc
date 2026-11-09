from pathlib import Path
import re,json,itertools,hashlib
p=Path('experiments/full_ram_export_lut_mutation_fixture_v1_2026-10-09');src=p/'design.blif';v=p/'VexRiscvFull_post_synthesis.v';text=v.read_text();lines=src.read_text().replace('\\\n',' ').splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   if lines[i].strip():rows.append(lines[i].split())
   i+=1
  tables[t[-1]]=(t[1:-1],rows)
edges={}
for body in re.findall(r'fpga_interconnect\s+\\\S+\s*\((.*?)\n    \);',text,re.S):
 a=re.search(r'\.datain\(\\(\S+)\s*\)',body);b=re.search(r'\.dataout\(\\(\S+)\s*\)',body)
 if a and b:edges[b[1]]=a[1]
for dst,source in re.findall(r'assign\s+\\(\S+)\s*=\s*\\(\S+)\s*;',text):edges[dst]=source
parent={}
def find(n):
 while n in parent:n=parent[n]
 return n
for q,(ins,rows) in tables.items():
 if len(ins)==1 and rows==[['1','1']]:
  a,b=find(q),find(ins[0])
  if a!=b:parent[a]=b
ram_outputs={}
for line in lines:
 t=line.split()
 if len(t)>1 and t[:2]==['.subckt','dual_port_ram']:
  pins=dict(item.split('=',1) for item in t[2:])
  atom=pins['out1']
  for index,port in [(0,'out1'),(1,'out2')]:
   key='dual_port_ram_'+atom+'_output_'+str(index)+'_0'
   assert key not in ram_outputs
   ram_outputs[key]=pins[port]
def logical(n):
 seen=set()
 while n in edges:
  if n in seen:raise ValueError('cycle')
  seen.add(n);n=edges[n]
 if n in ram_outputs:return find(ram_outputs[n])
 m=re.match(r'(?:lut|latch|\$_DFF_PP[01]_?)_(.+)_output_0_0$',n)
 if m:return find(m[1])
 return find(n.removesuffix('_output_0_0'))
records=[];issues=[]
pat=r'LUT_K\s*#\(\s*\.K\((\d+)\),\s*\.LUT_MASK\((\d+)\x27b([01]+)\)\s*\)\s*\\lut_(\S+)\s*\((.*?)\n    \);'
for k,width,mask,q,ports in re.findall(pat,text,re.S):
 if q not in tables:issues.append({'q':q,'reason':'source table missing'});continue
 ins,rows=tables[q];k=int(k);m=re.search(r'\.in\(\{(.*?)\}\)',ports,re.S)
 if m:tokens=re.findall(r'\\\S+|1\x27b[01xX]',m[1]);tokens=[x[1:] if x.startswith('\\') else x for x in reversed(tokens)]
 else:tokens=["1'b0"]*k
 if len(tokens)!=k:issues.append({'q':q,'reason':'token count'});continue
 resolved=[logical(t) if not t.startswith("1'b") else t for t in tokens];norm=[find(n) for n in ins]
 missing=set(norm)-set(resolved)
 if missing:issues.append({'q':q,'reason':'input binding missing','missing':sorted(missing),'resolved':resolved});continue
 failures=0;tested=0
 for bits in itertools.product([0,1],repeat=k):
  if any(t in ["1'b0","1'b1"] and bits[j]!=int(t[-1]) for j,t in enumerate(resolved)):continue
  values={t:bits[j] for j,t in enumerate(resolved) if not t.startswith("1'b")};logicalbits=[values[n] for n in norm]
  if not ins:expected=int(rows[0][0]) if rows else 0
  else:
   sense=int(rows[0][-1]) if rows else 1;hit=any(all(c=='-' or int(c)==bit for c,bit in zip(row[0],logicalbits)) for row in rows);expected=sense if hit else 1-sense
  actual=int(mask[-1-sum(bit<<j for j,bit in enumerate(bits))]);failures+=actual!=expected;tested+=1
 records.append({'q':q,'binary_cases':tested,'mismatches':failures})
 if failures:issues.append({'q':q,'reason':'truth mismatch','cases':failures})
o=Path('experiments/full_ram_export_lut_mutation_detection_v1_2026-10-09');o.mkdir();report={'bindings':{str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest() for x in [src,v,Path(__file__)]},'checked_luts':len(records),'binary_cases':sum(r['binary_cases'] for r in records),'issue_count':len(issues),'issues':issues,'records':records,'scope':'Binary LUT function and binding audit; unidentified aliases remain explicit failures, not Full sequential or four-state proof.'};(o/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['checked_luts','binary_cases','issue_count']}));print(json.dumps(issues[:5]))

assert len(records)==6461 and issues==[{'q':'const0','reason':'truth mismatch','cases':1}]
