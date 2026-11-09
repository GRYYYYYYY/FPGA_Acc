"""Index identity, ownership and candidate equivalence with admitted v1."""
import random,json,pathlib,hashlib
from array import array
from coupled_NET_tree_candidates_csr_v2 import CSRIndex,tree_candidate
from coupled_NET_tree_candidates_v1 import tree_candidate as reference
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/coupled_NET_tree_candidates_csr_core_v2_2026-10-19'
def main():
 O.mkdir(exist_ok=False);rng=random.Random(191021);arc_checks=0;tree_checks=0
 for trial in range(250):
  n=8;caps=array('I',[2]*n);kinds=['SOURCE']+['CHANX']*(n-2)+['SINK'];edges=[];offsets=array('Q',[0]);dest=array('I');cost=array('Q')
  for u in range(n):
   for v in range(1,n):
    if u!=n-1 and u!=v and (v==u+1 or rng.random()<.2):edges.append((len(edges),u,v,rng.randrange(4)));dest.append(v);cost.append(edges[-1][3])
   offsets.append(len(dest))
  index=CSRIndex(offsets,dest,cost,caps,kinds)
  for eid,u,v,w in edges:assert index.arc(eid)==(u,v,w);arc_checks+=1
  # Independent root DFS produces arbitrary simple paths, not only minima.
  candidates=[]
  def dfs(u,seen,path):
   if u==n-1:candidates.append(path);return
   for eid,a,b,w in edges:
    if a==u and b not in seen:dfs(b,seen|{b},path+[eid])
  dfs(0,{0},[])
  for path in candidates[:16]:
   a=tree_candidate(index,0,{7:path},{7:0},{7:100});b=reference(edges,0,{7:path},{7:0},{7:100},dict(enumerate(caps)),dict(enumerate(kinds)));assert a==b;tree_checks+=1
  original=index.arc(0);dest[0]=0;cost[0]=999;caps[0]=0;kinds[0]='SINK';offsets[1]=0;assert index.arc(0)==original and index.capacities[0]==2 and index.kinds[0]=='SOURCE'
 # Empty leading/interior/trailing CSR rows retain physical edge sources.
 q=CSRIndex([0,0,1,1,1,2,2],[2,5],[0,7],[1]*6,['SOURCE','SOURCE','CHANX','CHANX','CHANX','SINK']);assert q.arc(0)==(1,2,0) and q.arc(1)==(4,5,7)
 rejected=0
 for args in [([0,2,1],[1],[0],[1,1],['SOURCE','SINK']),([0,0,1],[2],[0],[1,1],['SOURCE','SINK']),([0,1,1],[1],[-1],[1,1],['SOURCE','SINK']),([0,1,1],[1],[0],[1,1],['SOURCE','BAD'])]:
  try:CSRIndex(*args)
  except ValueError:rejected+=1
  else:raise AssertionError('corrupt CSR admitted')
 for eid in [-1,2,True]:
  try:q.arc(eid)
  except ValueError:rejected+=1
  else:raise AssertionError('invalid edge ID admitted')
 out=dict(status='OWNED_CSR_EDGE_ID_AND_TREE_ADMISSION_EQUIVALENCE_PASS',graphs=250,physical_arcs_checked=arc_checks,trees_equal_v1=tree_checks,corruptions_rejected=rejected,owned_storage_input_mutation_isolation=True,empty_CSR_rows_pass=True,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [pathlib.Path(__file__).resolve(),R/'tools/coupled_NET_tree_candidates_csr_v2.py',R/'tools/coupled_NET_tree_candidates_v1.py']})
 (O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
