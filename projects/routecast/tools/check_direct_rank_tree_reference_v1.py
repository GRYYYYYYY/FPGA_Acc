"""Independent full-field candidate sets and pre-order trace replay on tiny trees."""
import json,random
from fractions import Fraction as F
from pathlib import Path
from direct_rank_tree_reference_v1 import train
from direct_rank_objective_v1 import components,objective
from exact_factor_elimination_v1 import sha

def main():
 rng=random.Random(20261020);decisions=0
 for trial in range(80):
  n=rng.randint(4,12);X=[[rng.randint(0,4) for _ in range(2)] for _ in range(n)];truth={i:rng.randrange(2) for i in range(n)};k=max(1,n//3);controls=[components({i:rng.randrange(2) for i in range(n)},truth,k)*2 for _ in range(2)]
  def evaluate(q):return objective([{'candidate':components(dict(enumerate(q)),truth,k)*2,'controls':controls}])
  model=train(X,evaluate,depth=2,minleaf=1);base=[0]*n if evaluate([0]*n)<=evaluate([1]*n) else [1]*n;position=0
  def replay(index,level,members):
   nonlocal position,decisions
   trace=model['trace'][position];position+=1;assert trace['node']==index;before=evaluate(base);assert before==trace['before'];proposals=[]
   if level<2:
    for feature in range(2):
     thresholds=sorted(set(X[i][feature] for i in members))[:-1]
     for threshold in thresholds:
      left=[i for i in members if X[i][feature]<=threshold];right=[i for i in members if X[i][feature]>threshold]
      for states in [(0,0),(0,1),(1,0),(1,1)]:
       q=base.copy()
       for i in members:q[i]=states[X[i][feature]>threshold]
       value=evaluate(q)
       if value<before:proposals.append((value,feature,threshold,states,q,left,right))
   node=model['nodes'][index]
   if not proposals:assert node['feature']==-1 and trace['choice'] is None and trace['after']==before
   else:
    best=min(proposals,key=lambda p:(p[0],p[1],p[2],p[3]));value,feature,threshold,states,q,left,right=best;assert trace['choice']==(feature,threshold,*states) and trace['after']==value;assert node['feature']==feature and node['threshold']==threshold;base[:]=q;replay(node['left'],level+1,left);replay(node['right'],level+1,right)
   decisions+=1
  replay(0,0,list(range(n)));assert base==model['points'] and position==len(model['trace']) and evaluate(base)==model['final_objective'] and model['final_objective']<=model['initial_objective']
 root=Path(__file__).resolve().parents[1];out=root/'experiments/direct_rank_tree_reference_contract_v1_2026-10-20';out.mkdir(exist_ok=False);files=[Path(__file__),root/'tools/direct_rank_tree_reference_v1.py',root/'experiments/direct_rank_objective_contract_v1_2026-10-20/verification.json'];v={'status':'PASS_TINY_TREE_ALL_CANDIDATE_INDEPENDENT_REPLAY','trees':80,'node_decisions':decisions,'bindings':{str(p):sha(p) for p in files},'scope':'Tiny depth2/minleaf1 reference only. Toy duplicated scopes exercise tree ordering, not native spatial construction. No real fit, scalable engine or heldout admission.'};(out/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],80,decisions)
if __name__=='__main__':main()
