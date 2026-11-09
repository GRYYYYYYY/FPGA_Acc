"""Prune accepted old native terminal paths without new graph/RC search."""
import re
from collections import defaultdict
from audit_native_route import NET,NODE
HEADER=re.compile(r'^Net\s+(\d+)\s+\((.*)\)(.*)$')
def scan(text):
 header=[];sections={};templates=defaultdict(dict);current=None;lines=[]
 for line in text.splitlines():
  h=HEADER.match(line)
  if h:
   if current is not None:sections[current]=lines
   current=h[2] if not h[3].strip() else None;lines=[line]
  elif not sections and current is None and not lines:header.append(line)
  elif current is not None:lines.append(line)
  m=NODE.match(line)
  if m:
   if current is None:raise ValueError('physical node under nonphysical header')
   key=int(m[1]),int(m[3]);prior=templates[current].get(key)
   if prior is not None and prior!=line:raise ValueError('ambiguous old node template')
   templates[current][key]=line
 if current is not None:sections[current]=lines
 return header,sections,templates

def render(paths,templates):
 if not paths:raise ValueError('empty partial NET')
 emitted=set();parents={};lines=[]
 for path in paths:
  if len(path)<2 or len({x[0] for x in path})!=len(path):raise ValueError('invalid/cyclic old path')
  for (u,_),(v,switch) in zip(path,path[1:]):
   if v in parents and parents[v]!=(u,switch):raise ValueError('inconsistent old tree parents')
   parents[v]=u,switch
  start=0
  if emitted:
   while start+1<len(path) and path[start+1][0] in emitted:start+=1
   if path[start][0] not in emitted or any(n in emitted for n,_ in path[start+1:]):raise ValueError('invalid old branch prefix')
  for i in range(start,len(path)):
   n=path[i][0];switch=path[i+1][1] if i+1<len(path) else -1;line=templates[n,switch];m=NODE.match(line)
   if m is None or int(m[1])!=n or (i==0 and m[2]!='SOURCE') or (i==len(path)-1 and m[2]!='SINK'):raise ValueError('old template terminal type mismatch')
   lines.append(line);emitted.add(n)
 return lines
