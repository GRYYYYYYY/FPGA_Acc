"""Ordinary-only source preflight: reject async primitives and audit every FF pin."""
import json,sys,ast,re,xml.etree.ElementTree as E
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=Path(sys.argv[1]).resolve();rp=Path(sys.argv[2]).resolve();r=json.loads(rp.read_text());files=r.get('files',r.get('native_8051_files',{}));assert files and all(sha(k)==v for k,v in r['bindings'].items()) and all(sha(k)==v for k,v in files.items());assert r.get('exit_code')==0 or (r.get('wrapper_exit_code')==1 and r.get('native_8051_log_reports_success'));net=out/'design.net';assert net.is_file();root=E.parse(net).getroot();parents={c:p for p in root.iter() for c in p};expected={}
blif=out/'design.blif'
for line in blif.read_text().splitlines():
 t=line.split()
 if len(t)>1 and t[0]=='.subckt' and t[1] in ['$_DFF_PP0_','$_DFF_PP1_']:
  pins=dict(x.split('=',1) for x in t[2:]);assert set(pins)=={'C','D','R','Q'} and pins['Q'] not in expected;expected[pins['Q']]=dict(model=t[1],pins=pins)
source=R/'tools/pre_route_endpoints.py';tree=ast.parse(source.read_text());function=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='resolve');from pre_route_endpoints import REF
function_source=ast.unparse(function);marker="own = context.attrib['instance']";assert function_source.count(marker)==1;line=next(x for x in function_source.splitlines() if marker in x);indent=line[:len(line)-len(line.lstrip())];replacement="siblings = [c for c in context.findall('block') if c.attrib['instance'] == instance]"+'\n'+indent+'if siblings:'+'\n'+indent+'    candidates = siblings'+'\n'+indent+'    break'+'\n'+indent+marker;function_source=function_source.replace(marker,replacement)
context=dict(parents={child:parent for parent in root.iter('block') for child in parent.findall('block')},memo={},REF=REF,re=re);exec(compile(function_source,str(Path(__file__)),'exec'),context);resolve=context['resolve']
jp=Path(sys.argv[3]).resolve();m=json.loads(jp.read_text())['modules'][sys.argv[4]];bits={'$false':'0','$true':'1','$undef':'x'}
for base,desc in m['netnames'].items():
 values=desc['bits'];offset=desc.get('offset',0);upto=desc.get('upto',0)
 for i,bit in enumerate(values):
  name=base if len(values)==1 and offset==0 and not upto else f'{base}[{offset+(len(values)-1-i if upto else i)}]';assert name not in bits or bits[name]==bit;bits[name]=bit
ordinary_expected={}
for line in blif.read_text().splitlines():
 t=line.split()
 if t and t[0]=='.latch':
  assert len(t)==6 and t[3]=='re' and t[2] not in ordinary_expected;ordinary_expected[t[2]]=dict(D=t[1],Q=t[2],clk=t[4],init=t[5])
ordinary_observed={}
observed={};types=Counter()
for block in root.iter('block'):
 if block.get('name')=='open' or list(block.findall('block')):continue
 parent=parents.get(block)
 if parent is None or parent.tag!='block' or parent.get('mode') not in ['reset_zero','reset_one']:continue
 assert block.get('instance')=='storage[0]';name=block.get('name');assert name in expected and name not in observed;mode=parent.get('mode');model='$_DFF_PP0_' if mode=='reset_zero' else '$_DFF_PP1_';assert expected[name]['model']==model
 inputs={p.get('name'):p.text.split() if p.text else [] for p in block.findall('inputs/port')};clocks={p.get('name'):p.text.split() if p.text else [] for p in block.findall('clocks/port')};outputs={p.get('name'):p.text.split() if p.text else [] for p in block.findall('outputs/port')}
 assert set(inputs)=={'D','R'} and set(clocks)=={'C'} and set(outputs)=={'Q'}
 assert all(len(values)==1 and values[0]!='open' for values in list(inputs.values())+list(clocks.values())+list(outputs.values()))
 resolved={pin:resolve(block,pin,0) for pin in ['D','R','C','Q']};assert all(value in bits and expected[name]['pins'][pin] in bits and bits[value]==bits[expected[name]['pins'][pin]] for pin,value in resolved.items()),(name,resolved,expected[name]['pins'])
 observed[name]=dict(model=model,resolved_signals=resolved,packed_inputs=inputs,packed_clocks=clocks,packed_outputs=outputs,original_pins=expected[name]['pins']);types[model]+=1
assert not expected and not observed, 'ordinary-only auditor rejects asynchronous primitive inputs'
for block in root.iter('block'):
 if block.get('name')=='open' or block.findall('block'):continue
 parent=parents.get(block)
 if parent is None or parent.tag!='block' or parent.get('mode')!='ordinary':continue
 assert block.get('instance')=='storage[0]';name=block.get('name');assert name in ordinary_expected and name not in ordinary_observed
 inputs={p.get('name'):p.text.split() if p.text else [] for p in block.findall('inputs/port')};clocks={p.get('name'):p.text.split() if p.text else [] for p in block.findall('clocks/port')};outputs={p.get('name'):p.text.split() if p.text else [] for p in block.findall('outputs/port')}
 assert set(inputs)=={'D'} and set(clocks)=={'clk'} and set(outputs)=={'Q'} and all(len(values)==1 and values[0]!='open' for values in list(inputs.values())+list(clocks.values())+list(outputs.values()))
 resolved={pin:resolve(block,pin,0) for pin in ['D','clk','Q']};assert all(value in bits and ordinary_expected[name][pin] in bits and bits[value]==bits[ordinary_expected[name][pin]] for pin,value in resolved.items()),(name,resolved,ordinary_expected[name]);ordinary_observed[name]=dict(resolved_signals=resolved,original_pins=ordinary_expected[name])
assert set(ordinary_observed)==set(ordinary_expected)

bindings={str(p):sha(p) for p in [Path(__file__),rp,net,blif,source,jp]};assert all(sha(k)==v for k,v in bindings.items())
auditout=Path(sys.argv[5]).resolve();auditout.mkdir(parents=True);(auditout/'ordinary_FF_signal_verification_v2.json').write_text(json.dumps(dict(bindings=bindings,primitive_counts=types,ordinary_FF_count=len(ordinary_observed),ordinary_FF_signals=ordinary_observed,all_ordinary_FF_names_and_nonopen_D_clk_Q_pins_match_original_bits=True,asynchronous_primitives_present=False,primitives=observed,scope='Packed atom identity and nonopen local pin wiring only. Hierarchical D/R/C/Q signals resolve to identical frozen JSON bits allowing proven aliases. Resolver extends bound endpoint extractor with nearest-ancestor child/sibling lookup required by internal leaf references; not independent of that resolver. Does not prove original HDL equivalence, or characterize reset recovery/removal timing. Not a native routing/heldout/netgain pass.'),indent=2)+'\n');print('PASS packed all FF pins',len(ordinary_observed),dict(types))
