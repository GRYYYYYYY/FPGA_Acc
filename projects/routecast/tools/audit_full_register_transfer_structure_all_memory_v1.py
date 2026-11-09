"""Conservative structural expression identity under explicit shared-state premises."""
import json,hashlib,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_start_all_memory_dependency_closure_v1_2026-10-09'
files=[E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json',E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json',P/'mapping_candidates.json',P/'register_driver_pairs.json']
s,m,c,r=[json.loads(f.read_text()) for f in files];s=next(iter(s['modules'].values()));m=next(iter(m['modules'].values()));sym_s={};sym_m={};conflicts=[]
for v in c['records']:
 b=v['source_bit'];xs=v['mapped_candidates'];sym_s[b]=('state',b)
 if len(xs)==1:
  x=xs[0]
  if isinstance(x,str):sym_s[b]=('literal',x)
  else:
   if x in sym_m and sym_m[x]!=('state',b):conflicts.append(x)
   sym_m[x]=('state',b)
assert not conflicts
sha=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def expressions(mod,syms):
 drivers={b:(n,v,p,i) for n,v in mod['cells'].items() for p,bs in v['connections'].items() if v['port_directions'][p]=='output' for i,b in enumerate(bs) if isinstance(b,int)};memo={};cells={};active=set();unknown=set()
 def bit(b):
  if isinstance(b,str):return sha(('literal',b))
  if b in syms:return sha(syms[b])
  if b in memo:return memo[b]
  if b not in drivers:unknown.add(b);return sha(('unmapped',id(mod),b))
  n,v,p,i=drivers[b]
  if re.match(r'^\$(?:[as]?dff|dlatch|mem)',v['type']):unknown.add(b);return sha(('uncut_state',id(mod),b))
  if n not in cells:
   assert n not in active;active.add(n)
   inputs={k:[bit(x) for x in bs] for k,bs in v['connections'].items() if v['port_directions'][k]=='input'}
   cells[n]=sha((v['type'],v['parameters'],inputs));active.remove(n)
  memo[b]=sha((cells[n],p,i));return memo[b]
 return bit,unknown
sb,su=expressions(s,sym_s);mb,mu=expressions(m,sym_m);records=[]
for v in r['records']:
 d=v['mapped_driver']
 if not d or d['type']=='$mux':continue
 src=s['cells'][v['source_cell']]; checks={}
 for port in ['D','EN','ARST','SRST']:
  if port not in src['connections']:continue
  si=v['source_lane'] if port=='D' else 0;mi=d['lane'] if port=='D' else 0
  x=src['connections'][port][si];y=d['connections'][port][mi];checks[port]={'source_bit':x,'mapped_bit':y,'structural_identity':sb(x)==mb(y)}
 records.append({'source_q':v['source_bit'],'mapped_q':v['mapped_candidates'][0],'checks':checks,'all_identical':all(c['structural_identity'] for c in checks.values())})
D=E/'full_register_transfer_structure_all_memory_v1_2026-10-09';D.mkdir(exist_ok=False);out={'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),*files]},'records':records,'identity_bits':sum(v['all_identical'] for v in records),'nonidentity_bits':sum(not v['all_identical'] for v in records),'unmapped_source_bits':sorted(su),'unmapped_structural_bits':sorted(mu),'scope':'Exact type/parameter/vector-input expression hashes with shared alias candidate boundary symbols and killReg=0. Identity is conditional expression correspondence; nonidentity is not inequivalence. Undefined literals matched symbolically, not arbitrary independent nondeterminism. No initial, induction, native export or Full admission.','functional_admission':False};(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['identity_bits','nonidentity_bits','unmapped_source_bits','unmapped_structural_bits']}))
