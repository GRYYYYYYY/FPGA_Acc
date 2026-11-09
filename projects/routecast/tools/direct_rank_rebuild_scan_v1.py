"""Independent scan: complete affected-case scoring, no sparse State/Fenwick."""
from direct_rank_objective_v1 import objective

def scan(features, domains, fields, members, minleaf=64):
 mapping=[(c,i) for c,(_,d) in enumerate(domains) for i in range(len(d.ids))]
 def energy(scores):return objective([{'candidate':s,'controls':d.controls} for (_,d),s in zip(domains,scores)])
 initial=[d.score(p) for (_,d),p in zip(domains,fields)];before=energy(initial);best=before;chosen=None;count=0
 for feature in range(len(features[0])):
  ordered=sorted(members,key=lambda row:(features[row][feature],row));groups=[]
  for row in ordered:
   value=features[row][feature]
   if not groups or groups[-1][0]!=value:groups.append((value,[]))
   groups[-1][1].append(row)
  for a,b in [(0,0),(0,1),(1,0),(1,1)]:
   full=[p.copy() for p in fields]
   for row in members:
    c,i=mapping[row];full[c][i]=b
   scores=[d.score(p) for (_,d),p in zip(domains,full)];cut=0
   for threshold,group in groups[:-1]:
    dirty=set()
    for row in group:
     c,i=mapping[row]
     if full[c][i]!=a:full[c][i]=a;dirty.add(c)
    for c in dirty:scores[c]=domains[c][1].score(full[c])
    cut+=len(group)
    if cut<minleaf or len(members)-cut<minleaf:continue
    value=energy(scores);key=(feature,threshold,a,b);count+=1
    if value<best or value==best and value<before and (chosen is None or key<chosen):best=value;chosen=key
 return {'before':before,'after':best,'choice':chosen,'candidates':count}
