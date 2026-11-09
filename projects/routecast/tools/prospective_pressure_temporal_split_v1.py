"""Temporal pressure/work split for independently admitted native traces."""
from collections import Counter

def split(stream,capacities):
 selected=False;current={};phase=None;first=None;first_end=None
 peak=Counter();area=Counter();frequency=Counter();work=[];checkpoints=[]
 while True:
  line=stream.readline()
  if not line:break
  w=line.split()
  if not w:raise ValueError('empty record')
  if w[0]==b'CP':
   assert not selected and len(w)==3
   phase=w[1];iteration=int(w[2]);selected=phase==b'iteration_end_after_local_opins';current={}
  elif selected and w[0]==b'V':
   assert len(w)==4
   n,occ,cap=map(int,w[1:]);assert 0<=n<len(capacities) and cap==capacities[n] and occ>cap and n not in current
   current[n]=occ-cap
  elif selected and w==[b'CE']:
   assert iteration==len(checkpoints)+1;checkpoints.append(dict(iteration=iteration,overflow_units=sum(current.values()),overused_nodes=len(current)))
   if iteration==1:first=dict(current);first_end=stream.tell()
   else:
    for n,v in current.items():peak[n]=max(peak[n],v);area[n]+=v;frequency[n]+=1
   selected=False
  elif w[0]==b'S':
   assert not selected and len(w)==6
   it,*values=map(int,w[1:]);assert it==len(work)+1 and all(x>=0 for x in values) and values[3]<=values[2]
   work.append(dict(iteration=it,**dict(zip(['NET_operations','connection_operations','heap_pushes','heap_pops'],values))))
 assert not selected and first is not None and len(work)==len(checkpoints)>=2
 assert [x['iteration'] for x in work]==[x['iteration'] for x in checkpoints]
 keys=['NET_operations','connection_operations','heap_pushes','heap_pops']
 return dict(first_overflow=first,first_checkpoint_end_byte=first_end,checkpoints=checkpoints,targets=dict(peak_overflow_units=dict(peak),sum_checkpoint_overflow_units=dict(area),checkpoints_overused=dict(frequency)),first_work={k:work[0][k] for k in keys},future_work={k:sum(x[k] for x in work[1:]) for k in keys},iteration_stats=work)
