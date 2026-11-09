"""Independent decimal raw-frontier join over all node records and summary counts."""
import json,sys
from pathlib import Path
from decimal import Decimal as N
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_full_rr_frontier_observer_v1_2026-10-19';D=E/'prospective_external_family_full_rr_frontier_comparison_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def parse(path):
 nodes={};support={};meta=[]
 for line in path.open():
  x=line.split()
  if x[0]=='N':nodes[int(x[1])]=(x[2],int(x[3]),N(x[4]),N(x[5]),N(x[6]),N(x[7]),int(x[8]))
  elif x[0]=='T':support[int(x[1])]=frozenset(map(int,x[4:]))
  elif x[0]=='F':meta=x[1:]
 return nodes,support,meta

def main():
 s=read(D/'summary.json');assert all(sha(p)==h for p,h in s['bindings'].items());old,ot,om=parse(I/'source/rr_frontier.tsv');rows=[]
 for row in s['rows']:
  case=row['case'];new,nt,nm=parse(I/case/'rr_frontier.tsv');assert old.keys()==new.keys() and ot[2]==nt[2];seen=set();counts=Counter();onnet=Counter();nonchannel=0
  for line in (D/case/'all_RR_comparison.jsonl').read_text().splitlines():
   r=json.loads(line);n=r['id'];assert n not in seen;seen.add(n);a,b=old[n],new[n];assert (a[0],a[1],a[6])==(b[0],b[1],b[6]);changed=[name for j,name in [(2,'occupancy'),(3,'history'),(4,'base'),(5,'present')] if a[j]!=b[j]];assert changed==r['changed_fields'] and r['type']==a[0] and r['on_NET2_prior_support']==(n in ot[2]);
   for field in changed:counts[a[0],field]+=1
   if 'occupancy' in changed:
    if a[0] not in ['CHANX','CHANY']:nonchannel+=1
    if n in ot[2]:onnet[a[0]]+=1
   for name,raw in [('old',a),('new',b)]:
    assert r[name]['type']==raw[0] and r[name]['capacity']==raw[1] and r[name]['cost_index']==raw[6]
    for j,k in [(2,'occupancy'),(3,'history'),(4,'base'),(5,'present')]:assert float(raw[j])==r[name][k]
  assert seen==old.keys() and len(seen)==row['nodes']==129090;assert counts=={(c['type'],c['field']):c['count'] for c in row['counts_by_type_and_field']};assert nonchannel==row['nonCHANNEL_occupancy_changed'] and dict(onnet)==row['NET2_prior_support_occupancy_changed_by_type'];assert om==row['boundary_metadata_source'] and nm==row['boundary_metadata_target'];rows.append(dict(case=case,nodes=len(seen)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL387270_RR_COMPARISON_ROWS_AND_VISIBLE_BOUNDARY_COUNTS_VERIFIED',rows=rows,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print('ALL387270_RR_FIELD_COMPARISONS_VERIFIED')
if __name__=='__main__':main()
