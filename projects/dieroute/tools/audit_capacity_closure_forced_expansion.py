"""Check whether every actual closure expansion is forced by unit-capacity conflicts."""
from pathlib import Path
import collections,csv,hashlib,json,mmap,struct
R=Path(__file__).resolve().parents[1]
def allocation(path):
 t=collections.defaultdict(set)
 with Path(path).open() as f:
  for row in csv.DictReader(f):t[int(row['net_id'])].update(int(row[k]) for k in ['source','parent','child'])
 return t
def main():
 output=R/'work/capacity_closure_forced_expansion_20261020';output.mkdir();refs={};results=[]
 protocols=[R/'work/elliptic_capacity_restore_closure_20261020/protocol.json']+[R/'work/capacity_closure_crosscase_20261020'/f'{c}_20x16_cw160_seed1/protocol.json' for c in ['apex2','frisc','elliptic']]
 for protocol in protocols:
  p=json.loads(protocol.read_text());base=allocation(p['baseline_tree']);cand=allocation(p['candidate_tree']);label=Path(p['candidate_tree']).parent.name
  resource=R/'work/width_coverage_native_costs_20261018'/label/'input.resources';used=set().union(*base.values(),*cand.values())
  with resource.open('rb') as f:
   m=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ);cap={v:struct.unpack_from('<H',m,16*v+2)[0] for v in used};m.close()
  seeds=[381,396] if '28x22' in label else [p['selected_seed']]
  for seed in seeds:
   restored={seed};waves=[]
   while True:
    owners=collections.defaultdict(set)
    for net in base:
     for node in base[net] if net in restored else cand[net]:owners[node].add(net)
    conflicts={v:ns for v,ns in owners.items() if len(ns)>cap[v]};hist=collections.Counter(cap[v] for v in conflicts);added=set().union(*conflicts.values())-restored if conflicts else set()
    forced=set().union(*(ns-restored for v,ns in conflicts.items() if cap[v]==1)) if conflicts else set()
    waves.append({'restored_nets':len(restored),'conflicting_capacity_histogram':dict(hist),'added_nets':len(added),'unit_conflict_forced_nets':len(forced)})
    if not conflicts:break
    assert added;restored.update(added)
   all_forced=all(w['added_nets']==w['unit_conflict_forced_nets'] for w in waves)
   results.append({'label':label,'seed':seed,'restored_nets':len(restored),'all_expansions_forced_by_unit_capacity':all_forced,'waves':waves})
  for f in [protocol,Path(p['baseline_tree']),Path(p['candidate_tree']),resource]:refs[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
 result={'status':'actual_whole_net_closure_forced_expansion_audited','cases':results,'proof_argument':'Both input allocations are capacity-legal. At a unit-capacity conflict, one restored net occupies its baseline node and another unrestored net occupies its candidate node. No feasible baseline/candidate mixture containing the current forced set can leave that unrestored owner unchanged. Inductively, if every addition is forced this way, the returned closure is a subset of every capacity-feasible mixture containing the seed.','scope':'Conditional least closure under complete baseline/candidate whole-net replacement and fixed seeds only. Does not rule out branch rerouting,alternate new trees,other seeds,or prove native quality. Generic algorithm still has no minimum guarantee for arbitrary multi-capacity conflicts.','source_sha256':refs,'research_complete':False}
 refs[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 with (output/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps([{k:v for k,v in row.items() if k!='waves'} for row in results]))
if __name__=='__main__':main()
