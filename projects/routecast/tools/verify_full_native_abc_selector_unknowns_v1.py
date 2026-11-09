"""Exhaust exact actual wrapper selector 0/1/X boundary valuations."""
import hashlib,itertools,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_native_blif_wrapper_selectors_v1_2026-10-09/selector_equivalence_audit.json';a=json.loads(P.read_text());drivers={b:c for c in a['native_cells'].values() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs};records=[]
def leaves(b,found):
 if isinstance(b,str):return
 if b not in drivers:found.add(b);return
 c=drivers[b];assert c['type']=='$_MUX_'
 for p in ['A','B','S']:leaves(c['connections'][p][0],found)
def evaluate(b,values):
 if isinstance(b,str):return b
 if b in values:return values[b]
 c=drivers[b]['connections'];s=evaluate(c['S'][0],values);av=evaluate(c['A'][0],values);bv=evaluate(c['B'][0],values)
 return av if s=='0' else bv if s=='1' else av if av==bv else 'x'
for target,_,_ in a['pairs']:
 table=a['abc_tables']['b'+str(target)];bits=[int(n[1:]) for n in table['inputs']];assert all(n=='b'+str(b) for n,b in zip(table['inputs'],bits));needed=set();leaves(target,needed);assert needed==set(bits)
 mismatch=[];cases=0
 for vals in itertools.product('01x',repeat=len(needed)):
  values=dict(zip(sorted(needed),vals));n=evaluate(target,values);outs=set()
  for binary in itertools.product('01',repeat=sum(values[b]=='x' for b in bits)):
   choices=iter(binary);assignment=''.join(next(choices) if values[b]=='x' else values[b] for b in bits);on=any(all(p=='-' or p==v for p,v in zip(row[0],assignment)) for row in table['rows']);outs.add('1' if on else '0')
  abc=next(iter(outs)) if len(outs)==1 else 'x';cases+=1
  if n!=abc:mismatch.append({'values':values,'native':n,'abc_consensus':abc})
 records.append({'target':target,'boundary_bits':sorted(needed),'cases':cases,'mismatches':mismatch})
out={'targets':len(records),'cases':sum(r['cases'] for r in records),'mismatch_count':sum(len(r['mismatches']) for r in records),'records':records,'input_sha256':hashlib.sha256(P.read_bytes()).hexdigest(),'scope':'Exhaust actual native two-mux ternary vs actual ABC truth-table compatible-binary consensus over shared 0/1/X selector boundary values. Excludes Z and proves no upstream state equality, init, macro ordering, exported LUT implementation or Full admission.'};D=E/'full_native_abc_selector_unknowns_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'unknown_selector_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['targets','cases','mismatch_count']},indent=2));assert out['mismatch_count']==0
