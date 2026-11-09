"""Conservative expression identity for merged register update inputs."""
import collections,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments'
P=E/'full_native_shared_register_updates_v1_2026-10-09/update_audit.json';F=E/'full_ram_mapping_candidate_v1_2026-10-09/structural.json';A=E/'full_structural_native_register_mapping_v1_2026-10-09/mapping_audit.json'
j=json.loads(P.read_text());m=max(json.loads(F.read_text())['modules'].values(),key=lambda m:len(m.get('cells',{})))
syms={}
for r in json.loads(A.read_text())['rows']:
 syms[r['bit']]=('held_state',r['bit'])
for n,p in m['ports'].items():
 if p['direction']=='input':
  for i,b in enumerate(p['bits']):syms[b]=('input',n,i)
drivers={b:(n,c,p,i) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for i,b in enumerate(bs) if isinstance(b,int)}
memo={};active=set();opaque=set()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def bit(b):
 if isinstance(b,str):return digest(('literal',b))
 if b in syms:return digest(syms[b])
 if b in memo:return memo[b]
 if b not in drivers:opaque.add(b);return digest(('undriven',b))
 assert b not in active
 active.add(b);n,c,p,i=drivers[b];co=c['connections'];t=c['type']
 if t=='$mux':x=(t,bit(co['A'][i]),bit(co['B'][i]),bit(co['S'][0]))
 elif t in ['$and','$or','$xor','$not']:
  vals=[]
  for port in ['A','B']:
   if port not in co:continue
   bs=co[port];v=bs[i] if i<len(bs) else bs[-1] if int(c['parameters'].get(port+'_SIGNED','0'),2) else '0';vals.append(bit(v))
  x=(t,vals)
 elif t=='dual_port_ram':opaque.add(b);x=('macro_output',b)
 else:x=(t,c['parameters'],{q:[bit(v) for v in bs] for q,bs in co.items() if c['port_directions'][q]=='input'},p,i)
 active.remove(b);memo[b]=digest(x);return memo[b]
records=[]
for g in j['records']:
 checks=[]
 base=g['members'][0]['signature']
 for member in g['members'][1:]:
  sig=member['signature'];ports={p: [bit(b) for b in bs] for p,bs in sig['inputs'].items()};baseline={p:[bit(b) for b in bs] for p,bs in base['inputs'].items()}
  checks.append({'cell':member['cell'],'lane':member['lane'],'equal':sig['type']==base['type'] and sig['parameters']==base['parameters'] and ports==baseline})
 records.append({'native_q':g['native_q'],'expression_identity':all(c['equal'] for c in checks),'checks':checks})
out={'groups':len(records),'identity_groups':sum(r['expression_identity'] for r in records),'nonidentity_groups':sum(not r['expression_identity'] for r in records),'opaque_bits':sorted(opaque),'records':records,'hashes':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P,F,A]},'scope':'Exact structural expression identities; every intermediate register Q remains an independent held-state symbol, so no merged-state equality is assumed to prove D identity. Undefined literals are symbolic literals, not independent nondeterministic values. Initial equality and native transfer remain unproved.'}
D=E/'full_native_shared_register_expressions_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'expression_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['records','hashes']},indent=2))
