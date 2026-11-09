"""Exact bounded (weighted cost, delay) labels under retained-tree constraints."""
import heapq,time

def search(f,rc,source,sink,initial,own,ledger,budget,spans,penalty,max_labels=10000,deadline=None,remaining_delay=None,forbidden_nodes=frozenset()):
 if penalty<0 or type(max_labels) is not int or max_labels<1:raise ValueError('invalid cost/label bound')
 labels=[];active={};heap=[];expanded=0
 def add(node,cost,delay,parent,eid):
  if node in forbidden_nodes:return False
  h=0 if remaining_delay is None else remaining_delay.get(node)
  if h is None or delay+h>budget:return False
  old=active.setdefault(node,[])
  if any(labels[i][1]<=cost and labels[i][2]<=delay for i in old if labels[i][5]):return False
  if len(labels)>=max_labels:return None
  for i in old:
   if cost<=labels[i][1] and delay<=labels[i][2]:labels[i][5]=False
  index=len(labels);labels.append([node,cost,delay,parent,eid,True]);old.append(index);heapq.heappush(heap,(cost+h,cost,delay,node,index));return True
 for node,delay in sorted(initial.items()):
  if add(node,delay,delay,None,None) is None:return dict(status='LABEL_LIMIT',labels_created=len(labels),expanded=expanded)
 while heap:
  estimate,cost,delay,u,index=heapq.heappop(heap)
  if not labels[index][5]:continue
  expanded+=1
  if expanded%1024==0 and deadline is not None and time.perf_counter()>deadline:return dict(status='DEADLINE',labels_created=len(labels),expanded=expanded)
  if u==sink:
   edges=[];cur=index
   while labels[cur][3] is not None:edges.append(labels[cur][4]);cur=labels[cur][3]
   edges.reverse();return dict(status='FOUND',join=labels[cur][0],physical_edge_ids=edges,delay=delay,cost=cost,labels_created=len(labels),expanded=expanded)
  for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
   v=f['dest_ranks'][slot]
   if v in own or ledger.get(v,0)-int(v in own)>=f['capacities'][v]:continue
   nd=delay+rc.increments[slot];nc=cost+rc.increments[slot]+penalty*spans[v]
   if add(v,nc,nd,index,f['edge_ids'][slot]) is None:return dict(status='LABEL_LIMIT',labels_created=len(labels),expanded=expanded)
 return dict(status='NO_BUDGET_CAPACITY_PATH',labels_created=len(labels),expanded=expanded)
