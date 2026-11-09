"""Bounded finite candidate CSP with pairwise arc consistency; no new paths."""
import json
from pathlib import Path
from collections import deque
from pre_route_endpoints import sha
from nonzero_rc_search_context import load
root=Path(__file__).resolve().parents[1]
parent=root/'experiments/nonzero_rc_multi_context_2026-10-06'
out=root/'experiments/nonzero_rc_utility_propagation_2026-10-06';out.mkdir()
r=json.loads((parent/'receipt.json').read_text());v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json')
_,_,nodes,f,rc,queries,_=load(root)
keys=[tuple(g['key']) for g in r['candidates']];paths=[g['paths'] for g in r['candidates']]
library_dir=root/'experiments/nonzero_rc_resolved_backjump_2026-10-06';library=json.loads((library_dir/'receipt.json').read_text());verified=json.loads((library_dir/'verification.json').read_text());assert verified['receipt_sha256']==sha(library_dir/'receipt.json') and library['parent_receipt_sha256']==sha(parent/'receipt.json');
from collections import Counter
utility=Counter()
pending=[library['proof']]
while pending:
 proof_node=pending.pop()
 for field in ('nogood','backjump'):
  if field in proof_node:utility[proof_node[field]]+=4
 pending.extend(c['proof'] for c in proof_node.get('children',[]))
for derivation in library['derivations']:
 if derivation['kind']=='resolution':utility.update(derivation['premises'])
selected_core_indices=sorted(range(len(library['nogoods'])),key=lambda i:(-utility[i],len(library['nogoods'][i]),i))[:256];clauses=[library['nogoods'][i] for i in selected_core_indices]
(out/'protocol.json').write_text(json.dumps({'parent_receipt_sha256':sha(parent/'receipt.json'),'state_limit':10000,'utility_selected_verified_cores':256,'library_sha256':sha(library_dir/'receipt.json'),'policy':'Fixed256 utility-ranked verified nogoods: prior hit/jump4, resolution-premise1, shorter/id tie, unit propagation alternating with AC3 binary compatibility, MRV then descending unresolved-neighbor degree then key tie, ascending candidate branches; exact original pool, no native reference paths; complete assignments checked for full union capacity','scope':'Binary propagation is necessary but not generally sufficient when capacities exceed1'},indent=2)+'\n')
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
states=0;pruned=0;limited=False;solution=None;unit_removals=0

def search(domains):
 global states,pruned,limited,solution,unit_removals
 if states>=10000:limited=True;return {'limit':True}
 states+=1;queue=deque(sorted(support));removals=[]
 while True:
  while queue:
   i,j=queue.popleft();old=domains[i];new=old
   for a in range(len(paths[i])):
    if old>>a&1 and not support[i,j][a]&domains[j]:new &= ~(1<<a);removals.append([i,a,j]);pruned+=1
   if new!=old:
    domains[i]=new
    if not new:return {'removals':removals,'empty':i}
    queue.extend((k,i) for k in sorted(neighbors[i]) if k!=j)
  changed=False
  for index,clause in enumerate(clauses):
   if any(not domains[i]>>a&1 for i,a in clause):continue
   uncertain=[(i,a) for i,a in clause if domains[i]!=(1<<a)]
   if len(uncertain)>1:continue
   i,a=uncertain[0] if uncertain else clause[0]
   domains[i]&=~(1<<a);removals.append([i,a,'nogood',index]);pruned+=1;unit_removals+=1;changed=True
   if not domains[i]:return {'removals':removals,'empty':i}
   queue.extend((k,i) for k in sorted(neighbors[i]))
  if not changed:break
 remaining=[i for i,d in enumerate(domains) if d.bit_count()>1]
 if not remaining:
  picked=[d.bit_length()-1 for d in domains];owners={};parents={}
  for i,a in enumerate(picked):
   for n in foot[i][a]:owners.setdefault(n,set()).add(keys[i][0])
   for n,p in incoming[i][a].items():parents.setdefault((keys[i][0],n),set()).add(p)
  if any(len(v)>f['capacities'][n] for n,v in owners.items()):return {'removals':removals,'capacity_dead':True}
  assert all(len(v)==1 for v in parents.values());solution=picked;return {'removals':removals,'solution':picked}
 i=min(remaining,key=lambda i:(domains[i].bit_count(),-sum(domains[j].bit_count()>1 for j in neighbors[i]),keys[i]));children=[]
 for a in range(len(paths[i])):
  if not domains[i]>>a&1:continue
  child_domains=domains.copy();child_domains[i]=1<<a;child=search(child_domains);children.append({'candidate':a,'proof':child})
  if solution is not None or limited:break
 return {'removals':removals,'branch':i,'children':children}
proof=search([(1<<len(ps))-1 for ps in paths]);status='COMPLETE_DIAGNOSTIC' if solution is not None else 'SELECTION_LIMIT' if limited else 'CANDIDATE_SET_UNSAT'
result={'unit_removals':unit_removals,'selected_core_indices':selected_core_indices,'library_sha256':sha(library_dir/'receipt.json'),'status':status,'states':states,'pruned_candidates':pruned,'selected':solution,'proof':proof,'parent_receipt_sha256':sha(parent/'receipt.json'),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(status,'states',states,'pruned',pruned,'unit_removals',unit_removals)
