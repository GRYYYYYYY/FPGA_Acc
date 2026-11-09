"""Bounded finite candidate CSP with pairwise arc consistency; no new paths."""
import json
from pathlib import Path
from collections import deque
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
root=Path(__file__).resolve().parents[1]
parent=root/'experiments/nonzero_rc_multi_context_2026-10-06'
out=root/'experiments/nonzero_rc_resolved_backjump_2026-10-06';out.mkdir()
r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json')
_,_,nodes,f,rc,queries,_=load(root)
keys=[tuple(g['key']) for g in r['candidates']];paths=[g['paths'] for g in r['candidates']]
(out/'protocol.json').write_text(json.dumps({'parent_receipt_sha256':sha(parent/'receipt.json'),'state_limit':10000,'policy':'AC3 binary compatibility, 32 verified minimized initial cores; reason-union and exhaustive-domain resolution nogood learning and backjump when failure core excludes current branch, MRV then descending unresolved-neighbor degree then key tie, ascending candidate branches; exact original pool, no native reference paths; complete assignments checked for full union capacity','scope':'Binary propagation is necessary but not generally sufficient when capacities exceed1'},indent=2)+'\n')
foot=[[set(p['nodes']) for p in ps] for ps in paths]
incoming=[[{n:(u,eid) for n,u,eid in p['parents']} for p in ps] for ps in paths]
support={};neighbors=[set() for _ in keys]
for i in range(len(keys)):
 for j in range(i+1,len(keys)):
  rows=[];reverse=[0]*len(paths[j]);restrict=False
  for a in range(len(paths[i])):
   mask=0
   for b in range(len(paths[j])):
    common=foot[i][a]&foot[j][b]
    valid=all(f['capacities'][n]>= (1 if keys[i][0]==keys[j][0] else 2) for n in common)
    if keys[i][0]==keys[j][0]:valid=valid and all(incoming[i][a][n]==incoming[j][b][n] for n in incoming[i][a].keys() & incoming[j][b].keys())
    if valid:mask|=1<<b;reverse[b]|=1<<a
    else:restrict=True
   rows.append(mask)
  if restrict:support[i,j]=rows;support[j,i]=reverse;neighbors[i].add(j);neighbors[j].add(i)
seed_dir=root/'experiments/nonzero_rc_minimized_conflicts_2026-10-06';seed=json.loads((seed_dir/'receipt.json').read_text());seed_verification=json.loads((seed_dir/'verification.json').read_text());assert seed_verification['receipt_sha256']==sha(seed_dir/'receipt.json') and seed['pool_sha256']==sha(parent/'receipt.json')
states=0;pruned=0;limited=False;solution=None;nogoods=[tuple(tuple(v) for v in c['core']) for c in seed['records']];known={ng:i for i,ng in enumerate(nogoods)};cache_hits=0;backjumps=0;derivations=[{'kind':'AC'} for _ in nogoods]

def remember(core,derivation):
 signature=tuple(sorted(core))
 if signature not in known:
  known[signature]=len(nogoods);nogoods.append(signature);derivations.append(derivation)
 return known[signature]

def search(domains,reasons,decisions):
 global states,pruned,limited,solution,cache_hits,backjumps
 if states>=10000:limited=True;return {'limit':True}
 states+=1
 for index,ng in enumerate(nogoods):
  if all(decisions.get(i)==a for i,a in ng):cache_hits+=1;return {'nogood':index}
 queue=deque(sorted(support));removals=[]
 while queue:
  i,j=queue.popleft();old=domains[i];new=old
  for a in range(len(paths[i])):
   if old>>a&1 and not support[i,j][a]&domains[j]:
    why=set()
    for b in range(len(paths[j])):
     if support[i,j][a]>>b&1:why.update(reasons[j,b])
    reasons[i,a]=frozenset(why);new &= ~(1<<a);removals.append([i,a,j]);pruned+=1
  if new!=old:
   domains[i]=new
   if not new:
    core=frozenset().union(*(reasons[i,a] for a in range(len(paths[i]))));signature=tuple(sorted(core))
    assert all(decisions.get(k)==a for k,a in signature)
    remember(signature,{'kind':'AC'})
    return {'removals':removals,'empty':i,'learned':known[signature]}
   queue.extend((k,i) for k in sorted(neighbors[i]) if k!=j)
 remaining=[i for i,d in enumerate(domains) if d.bit_count()>1]
 if not remaining:
  picked=[d.bit_length()-1 for d in domains];owners={};parents={}
  for i,a in enumerate(picked):
   for n in foot[i][a]:owners.setdefault(n,set()).add(keys[i][0])
   for n,p in incoming[i][a].items():parents.setdefault((keys[i][0],n),set()).add(p)
  if any(len(v)>f['capacities'][n] for n,v in owners.items()):return {'removals':removals,'capacity_dead':True}
  assert all(len(v)==1 for v in parents.values());solution=picked;return {'removals':removals,'solution':picked}
 i=min(remaining,key=lambda i:(domains[i].bit_count(),-sum(domains[j].bit_count()>1 for j in neighbors[i]),keys[i]));children=[];premises={}
 for a in range(len(paths[i])):
  if not domains[i]>>a&1:continue
  ds=domains.copy();rs=reasons.copy();decision=(i,a)
  for b in range(len(paths[i])):
   if ds[i]>>b&1 and b!=a:rs[i,b]=frozenset({decision})
  ds[i]=1<<a;child=search(ds,rs,{**decisions,i:a});children.append({'candidate':a,'proof':child})
  if solution is not None or limited:break
  conflict=child.get('nogood',child.get('learned',child.get('backjump',child.get('resolved'))))
  if conflict is not None:premises[a]=conflict
  if conflict is not None and all(k!=i for k,v in nogoods[conflict]):
   assert all(decisions.get(k)==v for k,v in nogoods[conflict]);backjumps+=1
   return {'removals':removals,'branch':i,'children':children,'backjump':conflict}
 if solution is None and not limited and len(premises)==domains[i].bit_count():
  for a in range(len(paths[i])):
   if not domains[i]>>a&1:premises[a]=remember(set(reasons[i,a])|{(i,a)},{'kind':'AC'})
  core=set()
  for index in premises.values():core.update((k,v) for k,v in nogoods[index] if k!=i)
  assert all(decisions.get(k)==v for k,v in core)
  index=remember(core,{'kind':'resolution','variable':i,'premises':[premises[a] for a in range(len(paths[i]))]})
  return {'removals':removals,'branch':i,'children':children,'resolved':index}
 return {'removals':removals,'branch':i,'children':children}
proof=search([(1<<len(ps))-1 for ps in paths],{},{});status='COMPLETE_DIAGNOSTIC' if solution is not None else 'SELECTION_LIMIT' if limited else 'CANDIDATE_SET_UNSAT'
result={'derivations':derivations,'seed_sha256':sha(seed_dir/'receipt.json'),'backjumps':backjumps,'nogoods':nogoods,'cache_hits':cache_hits,'status':status,'states':states,'pruned_candidates':pruned,'selected':solution,'proof':proof,'parent_receipt_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(status,'states',states,'pruned',pruned,'nogoods',len(nogoods),'cache_hits',cache_hits,'backjumps',backjumps)
