"""Bounded label-dependent diagnostic; exact local objective, no global optimum claim."""
from collections import Counter

def select(pools,initial,truth,domain,max_sweeps=16):
 if type(max_sweeps) is not int or max_sweeps<1 or set(initial)!=set(pools) or not pools:raise ValueError('selection domain')
 domain=set(domain)
 if any(type(n) is not int or n<0 for n in domain) or any(type(v) is not int or v<0 for v in truth.values()) or not set(truth)<=domain:raise ValueError('truth/domain')
 for net,choices in pools.items():
  if type(net) is not int or not choices or type(initial[net]) is not int or not 0<=initial[net]<len(choices) or any(not set(c)<=domain for c in choices):raise ValueError('candidate domain')
 selected=dict(initial);counts=Counter(n for net,choices in pools.items() for n in choices[selected[net]])
 def objective():return sum(abs(counts[n]-truth.get(n,0)) for n in domain)
 score=objective();start=score;moves=[];rounds=[]
 for sweep in range(max_sweeps):
  changed=0
  for net in sorted(pools):
   before=selected[net];old=pools[net][before];best=before;delta=0
   for i,choice in enumerate(pools[net]):
    d=sum(abs(counts[n]+(1 if n in choice else -1)-truth.get(n,0))-abs(counts[n]-truth.get(n,0)) for n in old^choice)
    if d<delta:best,delta=i,d
   if best==before:continue
   choice=pools[net][best]
   for n in old-choice:
    counts[n]-=1
    if not counts[n]:del counts[n]
   for n in choice-old:counts[n]+=1
   moves.append({'sweep':sweep,'net_id':net,'old_choice':before,'new_choice':best,'delta':delta,'before_L1':score,'after_L1':score+delta});score+=delta;selected[net]=best;changed+=1
  assert score==objective() and counts==Counter(n for net,choices in pools.items() for n in choices[selected[net]])
  rounds.append({'sweep':sweep,'moves':changed,'L1':score})
  if not changed:break
 return {'status':'ONE_NET_LOCAL_OPTIMUM' if not rounds[-1]['moves'] else 'SWEEP_LIMIT_NOT_OPTIMALITY_PROOF','selected':selected,'counts':dict(counts),'initial_L1':start,'final_L1':score,'moves':moves,'sweeps':rounds}
