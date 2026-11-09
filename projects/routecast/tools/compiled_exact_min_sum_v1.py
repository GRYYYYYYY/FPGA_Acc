"""Owned typed nonnegative tables and checked exact message/argmin kernel."""
from array import array
import ctypes as C
from math import prod
from pathlib import Path
R=Path(__file__).resolve().parents[1];BINARY=R/'build/exact_min_sum_v1_2026-10-20/minsum.so';U=C.c_uint64;P=C.POINTER(U);MAX=2**64-1
class Factor:
 def __init__(self,scope,values):
  self.scope=tuple(scope)
  if any(type(n) is not int for n in self.scope) or len(set(self.scope))!=len(self.scope):raise ValueError('factor scope')
  if isinstance(values,array):
   if values.typecode!='Q' or values.itemsize!=8:raise ValueError('unsigned64 table required')
   self.values=values
  else:
   if any(type(x) is not int or not 0<=x<=MAX for x in values):raise ValueError('factor cost domain')
   self.values=array('Q',values)
  if not len(self.values):raise ValueError('empty factor table')
class Message:
 def __init__(self,variable,separator,costs,argmin):self.variable=variable;self.separator=tuple(separator);self.factor=Factor(separator,costs);self.argmin=argmin

def _prepare(cards,variable,factors):
 if type(variable) is not int or variable not in cards or any(type(n) is not int or type(d) is not int or not 0<d<=MAX for n,d in cards.items()):raise ValueError('cardinalities')
 if any(type(f) is not Factor for f in factors):raise ValueError('factor type')
 variables={variable}|{n for f in factors for n in f.scope}
 if not variables<=set(cards):raise ValueError('unknown factor variable')
 separator=tuple(sorted(variables-{variable}));bag=(variable,*separator);dims=array('Q',[cards[n] for n in bag]);cells=prod(cards[n] for n in separator)
 if cells>MAX or cells*cards[variable]>MAX:raise ValueError('mixed-radix product exceeds unsigned64')
 strides=array('Q');lengths=array('Q');pointers=(P*len(factors))();owners=[]
 for i,f in enumerate(factors):
  if len(f.values)!=prod(cards[n] for n in f.scope):raise ValueError('factor table length')
  stride=1;mapping={}
  for n in reversed(f.scope):mapping[n]=stride;stride*=cards[n]
  strides.extend(mapping.get(n,0) for n in bag);lengths.append(len(f.values));owner=(U*len(f.values)).from_buffer(f.values);owners.append(owner);pointers[i]=C.cast(owner,P)
 return separator,bag,cells,dims,strides,lengths,pointers,owners

def _library():
 lib=C.CDLL(str(BINARY));signature=[U,P,U,P,P,C.POINTER(P),U,P,P]
 for name in ['rc_min_sum','rc_verify_min_sum']:getattr(lib,name).argtypes=signature;getattr(lib,name).restype=C.c_int
 return lib

def _call(name,prepared,factors,costs,args):
 sep,bag,cells,dims,strides,lengths,pointers,owners=prepared;arrays=[(U*len(a)).from_buffer(a) for a in [dims,strides,lengths,costs,args]];d,s,l,c,a=arrays
 return getattr(_library(),name)(len(bag),d,len(factors),s,l,pointers,cells,c,a)

def eliminate(cards,variable,factors,max_bytes=8*2**30,verify=True):
 prepared=_prepare(cards,variable,factors);separator,bag,cells=prepared[:3]
 if type(max_bytes) is not int or max_bytes<1:raise ValueError('message memory budget')
 if cells*(32 if verify else 16)>max_bytes:raise MemoryError('message plus verification scratch exceeds budget')
 costs=array('Q',[0])*cells;args=array('Q',[0])*cells;status=_call('rc_min_sum',prepared,factors,costs,args)
 if status:raise ValueError('min-sum kernel rejected '+str(status))
 message=Message(variable,separator,costs,args)
 if verify:verify_message(cards,variable,factors,message,max_bytes)
 return message

def verify_message(cards,variable,factors,message,max_bytes=8*2**30):
 if type(message) is not Message or message.variable!=variable:raise ValueError('message identity')
 prepared=_prepare(cards,variable,factors);separator,bag,cells=prepared[:3]
 if message.separator!=separator or len(message.factor.values)!=cells or message.factor.scope!=separator or len(message.argmin)!=cells or message.argmin.typecode!='Q':raise ValueError('message scope/length')
 if cells*32>max_bytes:raise MemoryError('independent verifier scratch exceeds budget')
 status=_call('rc_verify_min_sum',prepared,factors,message.factor.values,message.argmin)
 if status:raise ValueError('independent min-sum verification rejected '+str(status))
 return True
