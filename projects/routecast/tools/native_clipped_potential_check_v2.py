"""Persistent dense scratch arrays, fully cleared per native call; immutable RC.
Exact uint128 inequalities and arbitrary-integer fallback; one context per worker.
"""
import ctypes as C
import json
from array import array
from pathlib import Path
from pre_route_endpoints import sha
MAX=(1<<64)-1
U=C.c_uint64;P=C.POINTER(U)
def ptr(a):return C.cast(a.buffer_info()[0],P)
class PotentialCheck:
 def __init__(self,rc):
  self.rc=rc;self.f=rc.fields;self.n=len(self.f['node_ids']);self.native_calls=0;self.fallback_calls=0
  if not all(type(v) is int and v>=0 for v in rc.increments):raise ValueError('Nonnegative integer increments required')
  d=Path(__file__).resolve().parents[1]/'build/native_clipped_potential_check_v1_2026-10-08';p=d/'receipt.json';r=json.loads(p.read_text())
  if not all(sha(p)==h for p,h in r['bindings'].items()):raise ValueError('Stale checker build')
  self.bindings={**r['bindings'],str(p):sha(p)};self.lib=C.CDLL(str(d/'check.so'))
  self.lib.rc_check.argtypes=[U]*5+[P]*11;self.lib.rc_check.restype=C.c_int
  self.inc=array('Q',rc.increments) if all(v<=MAX for v in rc.increments) else None
  self.scratch=[array('Q',[0])*self.n for _ in range(5)]
  self.scratch_ptrs=[ptr(a) for a in self.scratch]
  self.snapshot={k:f for k,f in self.f.items()}
  self.inputs=([ptr(self.f[k]) for k in ('row_offsets','dest_ranks','switch_ids')]+[ptr(self.inc),ptr(self.f['capacities'])]+self.scratch_ptrs) if self.inc is not None else None
 def check(self,source,clip,pot,outside,parents):
  rc=self.rc;f=self.f;rc.node(source);initial=rc.initial(source)
  if rc.fields is not f or any(f.get(k) is not a for k,a in self.snapshot.items()):raise ValueError('Immutable graph snapshot replaced')
  if type(clip) is not int or clip<0 or type(initial) is not int or initial<0:raise ValueError('Invalid clip/initial')
  for n,v in pot.items():
   if type(n) is not int or not 0<=n<self.n or type(v) is not int or not 0<=v<clip or f['capacities'][n]<=0:raise ValueError('Invalid potential')
  for n,v in outside.items():
   if type(n) is not int or not 0<=n<self.n or type(v) is not int or v<0:raise ValueError('Invalid occupancy')
  for n,(u,s) in parents.items():
   if not all(type(x) is int for x in (n,u,s)) or not 0<=n<self.n or not 0<=u<self.n or not 0<=s<MAX:raise ValueError('Invalid fixed parent')
  if self.inc is None or initial>MAX or clip>MAX+1:
   self.fallback_calls+=1;checks=0
   if pot.get(source,clip)!=min(initial,clip):raise ValueError('Source potential mismatch')
   for u,a in pot.items():
    for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     v=f['dest_ranks'][e]
     if outside.get(v,0)<f['capacities'][v] and (v not in parents or parents[v]==(u,f['switch_ids'][e])):
      checks+=1
      if pot.get(v,clip)>a+rc.increments[e]:raise ValueError('Potential inequality violated')
   return checks
  for pointer in self.scratch_ptrs:C.memset(pointer,0,self.n*8)
  occ,ps,pw,values,present=self.scratch
  for n,v in outside.items():occ[n]=min(v,f['capacities'][n])
  for n,(u,s) in parents.items():ps[n]=u+1;pw[n]=s+1
  for n,v in pot.items():values[n]=v;present[n]=1
  checks=U();self.native_calls+=1
  code=self.lib.rc_check(self.n,source,initial,0 if clip==MAX+1 else clip,int(clip==MAX+1),*self.inputs,C.byref(checks))
  if code:raise ValueError('Native potential check rejected code '+str(code))
  return checks.value
