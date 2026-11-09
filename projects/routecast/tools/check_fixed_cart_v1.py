"""Every tiny split by Fraction, independent recursive groups and probability."""
import json,random,ctypes as C
from fractions import Fraction as F
from pathlib import Path
from compiled_fixed_cart_v1 import train,probability,matrix,library,BINARY
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def reference(X,Y,depth,minleaf):
 nodes=[]
 def build(members,level):
  at=len(nodes);positive=sum(Y[i] for i in members);N=len(members);node={'feature':-1,'left':-1,'right':-1,'rows':N,'positive':positive,'threshold':0.0};nodes.append(node)
  if level>=depth or N<2*minleaf or positive in [0,N]:return at
  score=F(positive*positive,N);best=None
  for f in range(len(X[0])):
   for threshold in sorted({X[i][f] for i in members})[:-1]:
    left=[i for i in members if X[i][f]<=threshold];right=[i for i in members if X[i][f]>threshold]
    if min(len(left),len(right))<minleaf:continue
    a=sum(Y[i] for i in left);b=sum(Y[i] for i in right);candidate=F(a*a,len(left))+F(b*b,len(right))
    if candidate>score:score=candidate;best=(f,threshold,left,right)
  if best is None:return at
  f,threshold,left,right=best;node.update(feature=f,threshold=float(threshold));node['left']=build(left,level+1);node['right']=build(right,level+1);return at
 build(list(range(len(X))),0);return nodes

def main():
 rng=random.Random(20261020);nodes=0;predictions=0
 for trial in range(400):
  n,d=rng.randrange(1,17),rng.randrange(1,6);X=[[rng.randrange(-3,4) for _ in range(d)] for _ in range(n)];Y=[rng.randrange(2) for _ in range(n)];depth=rng.randrange(5);minleaf=rng.randrange(1,5);actual=train(matrix(X,Y),depth,minleaf);expected=reference(X,Y,depth,minleaf);assert actual['nodes']==expected;nodes+=len(expected)
  for row in X+[[rng.randrange(-5,6) for _ in range(d)] for _ in range(8)]:
   at=0
   while expected[at]['feature']!=-1:
    node=expected[at];at=node['left'] if row[node['feature']]<=node['threshold'] else node['right']
   node=expected[at];assert probability(row,actual)==float(F(node['positive']+1,node['rows']+2));predictions+=1
 # Duplicated columns force exact gain ties; lower feature wins.
 tied=train(matrix([[0,0],[0,0],[1,1],[1,1]],[0,0,1,1]),2,1);assert tied['nodes'][0]['feature']==0 and tied['nodes'][0]['threshold']==0
 invalid=0
 for call in [lambda:train(matrix([[0]],[0]),depth=-1),lambda:train(matrix([[0]],[0]),minleaf=0),lambda:train(matrix([[0]],[0]),depth=True),lambda:probability([float('nan')],tied)]:
  try:call()
  except ValueError:invalid+=1
  else:raise AssertionError('invalid CART domain accepted')
 lib=library();x=(C.c_double*2)(0,1);y=(C.c_double*2)(0,1)
 for capacity,nan in [(1,False),(3,True)]:
  metadata=(C.c_int64*(5*capacity))(*([73]*(5*capacity)));thresholds=(C.c_double*capacity)(*([79]*capacity));count=C.c_uint64(83)
  if nan:x[0]=float('nan')
  assert lib.rc_fixed_cart(2,1,x,y,1,1,capacity,metadata,thresholds,C.byref(count))!=0 and list(metadata)==[73]*(5*capacity) and list(thresholds)==[79]*capacity and count.value==83;invalid+=1
 D=R/'experiments/fixed_cart_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/compiled_fixed_cart_v1.py',R/'tools/soft_demand_cpp/fixed_cart_v1.cpp',BINARY,R/'build/fixed_cart_v1_2026-10-20/receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL400_TINY_FRACTION_SPLITS_AND_FULL_TREES_PASS','tree_nodes':nodes,'predictions':predictions,'invalid_atomic_rejections':invalid,'bindings':{str(p):sha(p) for p in files},'scope':'Implementation exact split/tie policy only. Greedy depth-limited tree is not global tree optimum or calibrated probability/quality guarantee.'},indent=2)+'\n');print('CART_CONTRACT_PASS',nodes,predictions,invalid)
if __name__=='__main__':main()
