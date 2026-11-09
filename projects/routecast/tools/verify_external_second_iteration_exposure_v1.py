"""Independent first-two-iteration owner maps and allNET partition verification."""
import json,csv,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_iteration_support_observer_v1_2026-10-19';D=E/'prospective_external_family_second_iteration_exposure_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def load(path):
 frames={1:{},2:{}}
 for line in path.open():
  x=list(map(int,line.split()))
  if x[0]>2:break
  assert x[1] not in frames[x[0]];frames[x[0]][x[1]]=frozenset(x[3:])
 return frames

def crit(path):
 with path.open() as f:return {(int(r['net']),int(r['pin'])):float(r['criticality']) for r in csv.DictReader(f,delimiter='\t')}
def main():
 s=read(D/'summary.json');assert all(sha(p)==h for p,h in s['bindings'].items());a=load(I/'source/iteration_support.tsv');ca=crit(I/'source/initial_connections.tsv');rows=[]
 for r in s['rows']:
  case=r['case'];b=load(I/case/'iteration_support.tsv');cb=crit(I/case/'initial_connections.tsv');owner=[]
  for f in [a[1],b[1]]:
   owners=defaultdict(set)
   for net,ns in f.items():
    for n in ns:owners[n].add(net)
   owner.append(owners)
  delta={n for n in owner[0].keys()|owner[1].keys() if len(owner[0][n])!=len(owner[1][n])};over={n for n in delta if (len(owner[0][n])>1)!=(len(owner[1][n])>1)};assert len(delta)==r['first_demand_different_resources'] and len(over)==r['first_boolean_overuse_different_resources'];critical={n for n,p in ca if ca[n,p]!=cb[n,p]};records=read(D/case/'all_clean_NETs.json');counts=Counter();seen=set();new=[]
  for q in records:
   n=q['net_id'];assert n not in seen;seen.add(n);actual=(a[1][n]!=b[1][n],a[2][n]!=b[2][n],any(x in delta for x in a[1][n]|b[1][n]),any(x in over for x in a[1][n]|b[1][n]),n in critical);assert actual==tuple(q[k] for k in ['first_support_diff','second_support_diff','first_demand_difference_exposed','first_boolean_overuse_difference_exposed','initial_criticality_changed']);counts[actual]+=1
   if not actual[0] and actual[1]:new.append(actual)
  assert len(seen)==r['clean_NETs'];assert counts=={tuple(c[k] for k in ['first_diff','second_diff','count_exposed','boolean_exposed','initial_criticality_changed']):c['count'] for c in r['cells']};assert len(new)==r['new_second_round_divergences'];assert sum(x[2] for x in new)==r['new_count_exposed'];assert sum(x[4] for x in new)==r['new_initial_criticality_changed'];assert sum(x[2] or x[4] for x in new)==r['new_either_exposed'];rows.append(dict(case=case,all_clean_NETs=len(seen)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_OWNER_COUNT_CRITICALITY_AND_CLEAN_NET_PARTITIONS_INDEPENDENTLY_VERIFIED',rows=rows,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print('ALL3_EXPOSURE_PARTITIONS_VERIFIED')
if __name__=='__main__':main()
