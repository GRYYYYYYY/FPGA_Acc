"""Capacity-aware monotone baseline-net restoration, retaining all expansion evidence."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,struct
R=Path(__file__).resolve().parents[1];D=R/'work/elliptic_critical_net_restore_20261020'
def load(path):
 trees=collections.defaultdict(list)
 with Path(path).open() as f:
  for row in csv.DictReader(f):trees[int(row['net_id'])].append({k:row[k] for k in ['net_id','source','parent','child']})
 return trees
def main():
 p=json.loads((D/'protocol.json').read_text());base=load(p['baseline_tree']);cand=load(p['candidate_tree']);assert set(base)==set(cand)
 def nodes(t):return {int(v[k]) for v in t for k in ['source','parent','child']}
 bn={n:nodes(t) for n,t in base.items()};cn={n:nodes(t) for n,t in cand.items()}
 res=R/'work/width_coverage_native_costs_20261018/elliptic_28x22_cw320_seed1/input.resources';out=R/'work/elliptic_capacity_restore_closure_20261020';out.mkdir()
 result=[]
 with res.open('rb') as f:
  m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
  for arm in p['arms']:
   closure=set(arm['nets']);waves=[]
   while True:
    owners=collections.defaultdict(set)
    for n in base:
     for v in (bn[n] if n in closure else cn[n]):owners[v].add(n)
    conflicts={v:ns for v,ns in owners.items() if len(ns)>struct.unpack_from('<H',m,16*v+2)[0]}
    waves.append({'restored_nets':len(closure),'overused_resources':len(conflicts)})
    if not conflicts:break
    # Restore every current-state owner of a genuine conflict. All-baseline is
    # legal, hence any remaining conflict must have an unrestored owner.
    added=set().union(*conflicts.values())-closure;assert added
    closure.update(added)
   tree=out/(arm['name']+'.route_trees.csv')
   with tree.open('x') as stream:
    w=csv.DictWriter(stream,fieldnames=['net_id','source','parent','child']);w.writeheader()
    for n in sorted(base):w.writerows(base[n] if n in closure else cand[n])
   result.append({'name':arm['name'],'seed_nets':arm['nets'],'closure_net_ids':sorted(closure),'closure_nets':len(closure),'waves':waves,'final_capacity_conflicts':0,'tree':str(tree),'tree_sha256':hashlib.sha256(tree.read_bytes()).hexdigest()})
  m.close()
 files=[Path(p['baseline_tree']),Path(p['candidate_tree']),res,D/'protocol.json',Path(__file__).resolve()]
 def sha(p):
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  return h.hexdigest()
 a={'status':'capacity_aware_conflict_free_whole_net_mixtures_constructed','arms':result,'source_sha256':{str(f):sha(f) for f in files},'scope':'Monotone closure adds all unrestored owners only at actual overcapacity nodes. Sufficient but not minimal. Complete per-net baseline/candidate trees retained; native legality,STA,wirelength and modeled crossing checks required separately. No original cohort replacement or adoption.','adopted':False,'research_complete':False}
 with (out/'construction.json').open('x') as f:json.dump(a,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in x.items() if k not in ['closure_net_ids','tree','tree_sha256']} for x in result]))
if __name__=='__main__':main()
