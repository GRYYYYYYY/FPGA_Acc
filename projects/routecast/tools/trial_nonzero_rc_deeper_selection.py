"""Bounded finite candidate CSP with pairwise arc consistency; no new paths."""
import json
from pathlib import Path
from collections import deque
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
root=Path(__file__).resolve().parents[1]
parent=root/'experiments/nonzero_rc_multi_context_2026-10-06'
out=root/'experiments/nonzero_rc_deeper_selection_2026-10-06';out.mkdir()
r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json')
_,_,nodes,f,rc,queries,_=load(root)
keys=[tuple(g['key']) for g in r['candidates']];paths=[g['paths'] for g in r['candidates']]
(out/'protocol.json').write_text(json.dumps({'parent_receipt_sha256':sha(parent/'receipt.json'),'state_limit':50000,'policy':'AC3 binary compatibility, MRV key tie, ascending candidate branches; exact original pool, no native reference paths; complete assignments checked for full union capacity','scope':'Binary propagation is necessary but not generally sufficient when capacities exceed1'},indent=2)+'\n')
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
states=0;pruned=0;limited=False;solution=None

def search(domains):
 global states,pruned,limited,solution
 if states>=50000:limited=True;return {'limit':True}
 states+=1;queue=deque(sorted(support));removals=[]
 while queue:
  i,j=queue.popleft();old=domains[i];new=old
  for a in range(len(paths[i])):
   if old>>a&1 and not support[i,j][a]&domains[j]:new &= ~(1<<a);removals.append([i,a,j]);pruned+=1
  if new!=old:
   domains[i]=new
   if not new:return {'removals':removals,'empty':i}
   queue.extend((k,i) for k in sorted(neighbors[i]) if k!=j)
 remaining=[i for i,d in enumerate(domains) if d.bit_count()>1]
 if not remaining:
  picked=[d.bit_length()-1 for d in domains];owners={};parents={}
  for i,a in enumerate(picked):
   for n in foot[i][a]:owners.setdefault(n,set()).add(keys[i][0])
   for n,p in incoming[i][a].items():parents.setdefault((keys[i][0],n),set()).add(p)
  if any(len(v)>f['capacities'][n] for n,v in owners.items()):return {'removals':removals,'capacity_dead':True}
  assert all(len(v)==1 for v in parents.values());solution=picked;return {'removals':removals,'solution':picked}
 i=min(remaining,key=lambda i:(domains[i].bit_count(),keys[i]));children=[]
 for a in range(len(paths[i])):
  if not domains[i]>>a&1:continue
  child_domains=domains.copy();child_domains[i]=1<<a;child=search(child_domains);children.append({'candidate':a,'proof':child})
  if solution is not None or limited:break
 return {'removals':removals,'branch':i,'children':children}
proof=search([(1<<len(ps))-1 for ps in paths]);status='COMPLETE_DIAGNOSTIC' if solution is not None else 'SELECTION_LIMIT' if limited else 'CANDIDATE_SET_UNSAT'
result={'status':status,'states':states,'pruned_candidates':pruned,'selected':solution,'proof':proof,'parent_receipt_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(status,'states',states,'pruned',pruned)
