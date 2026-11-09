"""Qualified sparse sweep assembled into the frozen depth-first tree policy."""
from direct_rank_domain_v1 import training_objective
from direct_rank_split_sweep_v1 import scan

def train(features,domains,depth=8,minleaf=64):
 if type(depth) is not int or not 0<=depth<=8:raise ValueError('depth outside frozen limit')
 zeros=[[0]*len(d.ids) for _,d in domains];ones=[[1]*len(d.ids) for _,d in domains];v0=training_objective(domains,zeros);v1=training_objective(domains,ones);root=int(v1<v0);fields=ones if root else zeros;mapping=[(c,i) for c,(_,d) in enumerate(domains) for i in range(len(d.ids))];nodes=[];trace=[]
 # Preflight dimensions and membership even when depth0 skips all scans.
 scan(features,domains,fields,[],minleaf)
 def grow(members,level,state):
  index=len(nodes);nodes.append({'feature':-1,'left':-1,'right':-1,'state':state,'rows':len(members)})
  current=training_objective(domains,fields);result=scan(features,domains,fields,members,minleaf) if level<depth and len(members)>=2*minleaf else {'before':current,'after':current,'choice':None}
  assert result['before']==current
  trace.append({'node':index,'before':current,'after':result['after'],'choice':result['choice']})
  if result['choice'] is not None:
   feature,threshold,a,b=result['choice'];left=[];right=[]
   for row in members:
    target=left if features[row][feature]<=threshold else right;target.append(row);c,i=mapping[row];fields[c][i]=a if target is left else b
   nodes[index].update(feature=feature,threshold=threshold);nodes[index]['left']=grow(left,level+1,a);nodes[index]['right']=grow(right,level+1,b)
  return index
 grow(list(range(len(mapping))),0,root)
 return {'nodes':nodes,'points':[p for field in fields for p in field],'trace':trace,'initial_objective':min(v0,v1),'final_objective':training_objective(domains,fields)}
