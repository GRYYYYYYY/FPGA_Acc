from pathlib import Path
import re,json,itertools,hashlib
p=Path('experiments/full_ram_init_export_runtime_v7_2026-10-09');src=p/'design.blif';v=p/'VexRiscvFull_post_synthesis.v';text=v.read_text();lines=src.read_text().replace('\\\n',' ').splitlines();tables={};i=0
while i<len(lines):
 t=lines[i].split();i+=1
 if t and t[0]=='.names':
  rows=[]
  while i<len(lines) and not lines[i].lstrip().startswith('.'):
   if lines[i].strip() and not lines[i].lstrip().startswith('#'):rows.append(lines[i].split())
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
def pins(body):
 result={}
 for port,expr in re.findall(r'\.(\w+)\((.*?)\)',body,re.S):
  tokens=re.findall(r'\\\S+|1\x27b[01xX]',expr)
  result[port]=[t[1:] if t.startswith('\\') else t for t in reversed(tokens)]
 return result
source_latches={};source_resets={};source_rams={}
for line in lines:
 t=line.split()
 if t and t[0]=='.latch':source_latches[t[2]]=dict(D=t[1],clk=t[4],init=t[5])
 if len(t)>1 and t[0]=='.subckt':
  d=dict(x.split('=',1) for x in t[2:])
  if t[1].startswith('$_DFF_PP'):source_resets[d['Q']]=(t[1],d)
  if t[1]=='dual_port_ram':source_rams[d['out1']]=d
def compare(kind,name,actual,expected):
 for port,nets in expected.items():
  want=[find(n) for n in nets];got=[logical(n) if not n.startswith("1'b") else n for n in actual.get(port,[])]
  if got!=want:issues.append(dict(kind=kind,name=name,port=port,expected=want,actual=got))
 records.append(dict(kind=kind,name=name,input_pins=sum(map(len,expected.values()))))
seen=set()
for init,name,body in re.findall(r'DFF\s*#\(\s*\.INITIAL_VALUE\(1\x27b([01x])\)\s*\)\s*\\latch_(\S+)\s*\((.*?)\n    \);',text,re.S):
 d=source_latches[name];compare('ordinary',name,pins(body),{'D':[d['D']],'clk':[d['clk']]});seen.add(name)
 assert init==('x' if d['init'] in ['2','3'] else d['init'])
assert seen==set(source_latches)
seen=set()
for model,name,body in re.findall(r'(\$_DFF_PP[01]_)\s*#\(\s*\)\s*\\\$_DFF_PP[01]__(\S+)\s*\((.*?)\n    \);',text,re.S):
 wanted,d=source_resets[name];assert model==wanted;compare('reset',name,pins(body),{k:[d[k]] for k in ['C','D','R']});seen.add(name)
assert seen==set(source_resets)
seen=set()
for name,body in re.findall(r'dual_port_ram\s*#\(.*?\)\s*\\dual_port_ram_(\S+)\s*\((.*?)\n    \);',text,re.S):
 d=source_rams[name];expected={'clock':[d['clk']],**{k:[d[k]] for k in ['data1','data2','we1','we2']},**{k:[d[k+'['+str(i)+']'] for i in range(10)] for k in ['addr1','addr2']}}
 compare('ram',name,pins(body),expected);seen.add(name)
assert len(seen)==174
out=Path('experiments/full_ram_export_sequential_inputs_v2_2026-10-09');out.mkdir();report={'bindings':{str(x.resolve()):hashlib.sha256(x.read_bytes()).hexdigest() for x in [src,v,Path(__file__)]},'records':records,'issues':issues,'issue_count':len(issues),'cells':len(records),'input_pins':sum(r['input_pins'] for r in records),'scope':'Source-to-export sequential input connectivity and ordinary init/model type checks; not state transition equivalence, four-state or physical initialization.'};(out/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['cells','input_pins','issue_count']}));print(json.dumps(issues[:5]));assert not issues
