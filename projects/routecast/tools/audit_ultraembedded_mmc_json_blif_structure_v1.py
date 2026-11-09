"""Exhaustive per-gate truth/pin, FF clock/init and all-port equality of actual JSON/BLIF."""
import sys,json,itertools
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
src=R/'experiments/ultraembedded_peripheral_frontends_v1_2026-10-08';receipt=json.loads((src/'receipt.json').read_text());protocol=json.loads((src/'protocol.json').read_text());out=R/'experiments/ultraembedded_mmc_json_blif_structure_v1_2026-10-08';out.mkdir();bindings={**closure([Path(__file__)]),str(src/'receipt.json'):sha(src/'receipt.json')};rows=[]
for case in protocol['cases']:
 name=case['name']
 if name!='mmc':continue
 jp=src/name/'design.json';bp=src/name/'design.blif';f=next(r['files'] for r in receipt['rows'] if r['name']==name)
 assert sha(jp)==f[str(jp)]
 assert sha(bp)==f[str(bp)] and all(sha(k)==v for k,v in receipt['bindings'].items());bindings.update({str(p):sha(p) for p in [jp,bp,src/'protocol.json']})
 m=json.loads(jp.read_text())['modules'][case['top']];names={'$false':'0','$true':'1','$undef':'x'};initial={};ports={}
 def expand(base,desc):
  bits=desc['bits'];offset=desc.get('offset',0);upto=desc.get('upto',0)
  return [(base if len(bits)==1 and offset==0 and not upto else f'{base}[{offset+(len(bits)-1-i if upto else i)}]',bit) for i,bit in enumerate(bits)]
 for base,desc in m['netnames'].items():
  for wire,bit in expand(base,desc):
   if wire in names:assert names[wire]==bit
   names[wire]=bit
  if 'init' in desc['attributes']:
   values=desc['attributes']['init'][::-1];assert len(values)==len(desc['bits'])
   for bit,value in zip(desc['bits'],values):
    if bit in initial:assert initial[bit]==value
    initial[bit]=value
 for base,desc in m['ports'].items():
  for wire,bit in expand(base,desc):ports[wire]=(desc['direction'],bit)
 expected=Counter();actual=Counter();alias=0;blifports={};lines=[s.strip() for s in bp.read_text().splitlines() if s.strip() and not s.lstrip().startswith('#')];i=0
 for cell in m['cells'].values():
  t=cell['type'];c=cell['connections']
  if t=='$_DFF_P_':expected[('ff',c['D'][0],c['Q'][0],c['C'][0],initial.get(c['Q'][0],'x'))]+=1;continue
  if t=='$scopeinfo':assert not c;continue
  if t=='$print':raise AssertionError('No print projection admitted for fixed pair')
  if t in ['$_DFF_PP0_','$_DFF_PP1_']:
   assert set(c)=={'C','D','Q','R'} and all(len(v)==1 for v in c.values()) and initial.get(c['Q'][0],'x')=='x';expected[('async',t,tuple((k,c[k][0]) for k in sorted(c)))]+=1;continue
  args={'$_MUX_':['A','B','S'],'$_XOR_':['A','B'],'$_XNOR_':['A','B'],'$_NOT_':['A'],'$_OR_':['A','B'],'$_AND_':['A','B']}[t];inputs=tuple(c[k][0] for k in args)
  def evaluate(v):
   if t=='$_MUX_':return v[1] if v[2] else v[0]
   if t=='$_XOR_':return v[0]^v[1]
   if t=='$_XNOR_':return 1-(v[0]^v[1])
   if t=='$_NOT_':return 1-v[0]
   if t=='$_OR_':return v[0]|v[1]
   return v[0]&v[1]
  expected[('gate',inputs,c['Y'][0],tuple(evaluate(v) for v in itertools.product([0,1],repeat=len(args))))]+=1
 while i<len(lines):
  tok=lines[i].split();i+=1
  if tok[0] in ['.inputs','.outputs']:
   for wire in tok[1:]:assert wire not in blifports;blifports[wire]=('input' if tok[0]=='.inputs' else 'output',names[wire])
  elif tok[0]=='.latch':
   assert len(tok)==6 and tok[3]=='re';actual[('ff',names[tok[1]],names[tok[2]],names[tok[4]],{'0':'0','1':'1','2':'x','3':'x'}[tok[5]])]+=1
  elif tok[0]=='.subckt':
   assert tok[1] in ['$_DFF_PP0_','$_DFF_PP1_'];pins=dict(x.split('=',1) for x in tok[2:]);assert len(pins)==len(tok)-2 and set(pins)=={'C','D','Q','R'};actual[('async',tok[1],tuple((k,names[pins[k]]) for k in sorted(pins)))]+=1
  elif tok[0]=='.names':
   inputs=tok[1:-1];output=tok[-1];cubes=[]
   while i<len(lines) and not lines[i].startswith('.'):
    cube=lines[i].split();i+=1;assert (len(cube)==2 if inputs else len(cube)==1);cubes.append(cube)
   if not inputs:
    if output=='$undef':assert not cubes;continue
    assert names[output] in ['0','1'] and bool(cubes)==(names[output]=='1');continue
   assert len(inputs)<=6
   truth=[]
   for values in itertools.product([0,1],repeat=len(inputs)):
    selected=[int(c[1]) for c in cubes if all(p=='-' or int(p)==v for p,v in zip(c[0],values))];assert all(len(c[0])==len(inputs) and c[1] in ['0','1'] for c in cubes);assert len(set(selected))<=1;truth.append(selected[0] if selected else (1-int(cubes[0][1]) if cubes and cubes[0][1]=='0' else 0))
   pins=tuple(names[x] for x in inputs);target=names[output]
   if len(pins)==1 and pins[0]==target and tuple(truth)==(0,1):alias+=1;continue
   actual[('gate',pins,target,tuple(truth))]+=1
  else:assert tok[0] in ['.model','.end']
 assert ports==blifports;assert actual==expected,(name,len(actual-expected),len(expected-actual),list((actual-expected).items())[:1]);rows.append({'name':name,'gates':sum(v for k,v in expected.items() if k[0]=='gate'),'flipflops':sum(v for k,v in expected.items() if k[0]=='ff'),'asynchronous_flipflops':sum(v for k,v in expected.items() if k[0]=='async'),'alias_buffers':alias,'all_ports_truth_tables_pins_clocks_initial_states_exact':True});print(name,'STRUCTURE PASS',flush=True)
(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows,'scope':'Exact serialized hardware graph: gates, FF clock/init, asynchronous primitive types/ports and top ports; no print cells permitted, scope metadata excluded. Asynchronous behavioral semantics inherited by primitive identity, not simulated or original HDL equivalence proven, not original HDL synthesis equivalence or native route proof.'},indent=2)+'\n')
